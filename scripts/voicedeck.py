#!/usr/bin/env python3
"""VoiceDeck — озвучка учебных текстов нейроголосами Microsoft.

    say     одна фраза -> normal + slow + субтитры (+ shadow-микс)
    batch   файл с фразами -> mp3-пачка + TSV для Anki
    dialog  диалог "Имя: реплика" -> реплики разными голосами + склейка + плейлист
    cards   TSV "фраза-перевод" -> карточки с озвучкой обеих сторон
    voices  пресеты голосов (и живой список с --live)
    selfcheck  проверки без сети

Зависимости: edge-tts. ffmpeg — опционально, только для склеек.
"""

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

try:
    import edge_tts
except ImportError:  # pragma: no cover
    sys.exit("Нет модуля edge-tts. Поставь: pip install edge-tts")

# techdebt: пресеты зашиты в код вместо конфига — хватает до ~20 голосов,
# дальше вынести в voices.json с выбором dialect/age/style.

PRESETS = {
    # английский
    "en-us-f": "en-US-JennyNeural",
    "en-us-m": "en-US-GuyNeural",
    "en-us-f2": "en-US-AriaNeural",
    "en-gb-f": "en-GB-SoniaNeural",
    "en-gb-m": "en-GB-RyanNeural",
    # немецкий
    "de-f": "de-DE-KatjaNeural",
    "de-m": "de-DE-ConradNeural",
    "de-f2": "de-DE-SeraphinaMultilingualNeural",
    "de-m2": "de-DE-FlorianMultilingualNeural",
    # русский (обороты карточек)
    "ru-f": "ru-RU-SvetlanaNeural",
    "ru-m": "ru-RU-DmitryNeural",
}

VOICE_RE = re.compile(r"^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$")
RATE_RE = re.compile(r"^[+-]\d+%$")
PITCH_RE = re.compile(r"^[+-]\d+Hz$")


def resolve_voice(spec: str) -> str:
    """Пресет (de-f) или полное имя (de-DE-KatjaNeural) -> полное имя."""
    if spec in PRESETS:
        return PRESETS[spec]
    if VOICE_RE.fullmatch(spec):
        return spec
    raise ValueError(f"Неизвестный голос '{spec}'. Пресеты: {', '.join(sorted(PRESETS))}")


def check_rate(value: str) -> str:
    if not RATE_RE.fullmatch(value):
        raise ValueError(f"Темп должен быть вида +0%/-30%, получил '{value}'")
    return value


def check_pitch(value: str) -> str:
    if not PITCH_RE.fullmatch(value):
        raise ValueError(f"Тон должен быть вида +0Hz/-20Hz, получил '{value}'")
    return value


def slugify(text: str, limit: int = 40) -> str:
    """Груße Welt! -> grusse-welt. Только ASCII, безопасно для файлов и Anki."""
    text = text.replace("ß", "ss").replace("ẞ", "SS")
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    return (slug[:limit].rstrip("-") or "line")


def read_lines(path: Path) -> list[str]:
    """Непустые строки, '#' в начале — комментарий."""
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    if not out:
        raise ValueError(f"В {path} нет ни одной строки для озвучки")
    return out


def split_card(line: str) -> tuple[str, str]:
    """'фраза \\t перевод' -> (фраза, перевод). Без таба — перевод пустой."""
    front, _, back = line.partition("\t")
    return front.strip(), back.strip()


def parse_dialog(lines: list[str]) -> list[tuple[str, str]]:
    """'Анна: Привет!' -> (Анна, Привет!). Строка без ':' — ремарка рассказчика."""
    out = []
    for line in lines:
        speaker, sep, text = line.partition(":")
        if sep and speaker.strip() and " " not in speaker.strip() and len(speaker.strip()) <= 20:
            out.append((speaker.strip(), text.strip()))
        else:
            out.append(("", line.strip()))
    return out


def parse_cast(spec: str) -> dict[str, str]:
    """'Анна=de-f,Бен=de-m' -> {Анна: de-f, ...}."""
    cast = {}
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, sep, voice = chunk.partition("=")
        if not sep or not name.strip() or not voice.strip():
            raise ValueError(f"Плохая роль '{chunk}'. Формат: Имя=голос,Имя=голос")
        cast[name.strip()] = voice.strip()
    return cast


def assign_voices(
    replicas: list[tuple[str, str]],
    cycle: list[str],
    cast: dict[str, str],
    narrator: str,
) -> list[tuple[str, str, str]]:
    """Каждой реплике — голос: cast для знакомых, остальные по кругу."""
    order: dict[str, str] = {}
    out = []
    for speaker, text in replicas:
        if speaker in cast:
            voice = cast[speaker]
        elif speaker in order:
            voice = order[speaker]
        elif speaker == "":
            voice = narrator
        else:
            voice = cycle[len(order) % len(cycle)]
            order[speaker] = voice
        out.append((speaker, text, voice))
    return out


async def synth(
    text: str,
    voice: str,
    mp3_path: Path,
    srt_path: Path | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    proxy: str | None = None,
) -> None:
    """Один запрос: аудио всегда, субтитры — если нужен srt_path."""
    boundary = "WordBoundary" if srt_path else "SentenceBoundary"
    communicate = edge_tts.Communicate(
        text, resolve_voice(voice), rate=rate, volume=volume, pitch=pitch,
        boundary=boundary, proxy=proxy,
    )
    submaker = edge_tts.SubMaker() if srt_path else None
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mp3_path, "wb") as audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif submaker is not None and chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
    if submaker is not None and srt_path is not None:
        srt_path.write_text(submaker.get_srt(), encoding="utf-8")


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def ffmpeg_concat(parts: list[Path], dest: Path, gap: float = 0.8) -> None:
    """Склейка mp3 с паузой gap между кусками (пауза — место для повтора)."""
    if not have_ffmpeg():
        raise RuntimeError("Нет ffmpeg в PATH — склейка невозможна")
    with tempfile.TemporaryDirectory() as tmp:
        silence = Path(tmp) / "sil.mp3"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono:d={gap}",
             "-c:a", "libmp3lame", str(silence)],
            check=True,
        )
        seq: list[Path] = []
        for part in parts:
            seq.append(part)
            seq.append(silence)
        seq.pop()  # пауза после последнего куска не нужна
        inputs: list[str] = []
        for part in seq:
            inputs += ["-i", str(part)]
        filt = "".join(f"[{i}:a]" for i in range(len(seq)))
        filt += f"concat=n={len(seq)}:v=0:a=1[out]"
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
             "-filter_complex", filt, "-map", "[out]", "-c:a", "libmp3lame", str(dest)],
            check=True,
        )


def write_playlist(files: list[Path], dest: Path) -> None:
    dest.write_text("#EXTM3U\n" + "\n".join(p.name for p in files) + "\n", encoding="utf-8")


def write_manifest(entries: list[dict], dest: Path) -> None:
    dest.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


async def run_jobs(coros: list, jobs: int) -> list:
    """Параллельный запуск с лимитом одновременных запросов."""
    sem = asyncio.Semaphore(max(1, jobs))

    async def guarded(coro):
        async with sem:
            return await coro

    return await asyncio.gather(*[guarded(c) for c in coros], return_exceptions=True)


# --- команды ---

async def cmd_say(args) -> int:
    slug = slugify(args.text)
    normal = args.out / f"{slug}.mp3"
    slow = args.out / f"{slug}@slow.mp3"
    srt = args.out / f"{slug}.srt" if not args.no_sub else None
    await run_jobs([
        synth(args.text, args.voice, normal, srt, "+0%", args.volume, args.pitch, args.proxy),
        synth(args.text, args.voice, slow, None, args.slow_rate, args.volume, args.pitch, args.proxy),
    ], args.jobs)
    print(f"normal: {normal}\nslow:   {slow}")
    if srt:
        print(f"subs:   {srt}")
    if not args.no_shadow:
        if have_ffmpeg():
            shadow = args.out / f"{slug}@shadow.mp3"
            ffmpeg_concat([slow, normal], shadow, gap=args.gap)
            print(f"shadow: {shadow}  (slow + пауза + normal — для shadowing)")
        else:
            print("WARN: нет ffmpeg — shadow-микс пропущен (normal/slow на месте)")
    return 0


def item_files(deck: Path, idx: int, text: str) -> tuple[Path, Path, Path]:
    base = f"{idx:03d}-{slugify(text)}"
    return deck / f"{base}.mp3", deck / f"{base}@slow.mp3", deck / f"{base}.srt"


async def cmd_batch(args) -> int:
    deck = args.out / args.deck
    deck.mkdir(parents=True, exist_ok=True)
    lines = read_lines(Path(args.file))
    jobs, manifest, tsv = [], [], []
    for i, line in enumerate(lines, 1):
        phrase, trans = split_card(line)
        normal, slow, srt = item_files(deck, i, phrase)
        jobs.append(synth(phrase, args.voice, normal, srt, "+0%", args.volume, args.pitch, args.proxy))
        if not args.no_slow:
            jobs.append(synth(phrase, args.voice, slow, None, args.slow_rate, args.volume, args.pitch, args.proxy))
        manifest.append({"file": normal.name, "slow": None if args.no_slow else slow.name,
                         "text": phrase, "trans": trans, "voice": args.voice, "rate": "+0%"})
        cell = f"{phrase} [sound:{normal.name}]"
        tsv.append(f"{cell}\t{trans}" if trans else cell)
    results = await run_jobs(jobs, args.jobs)
    failed = sum(1 for r in results if isinstance(r, Exception))
    (deck / "anki.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    write_manifest(manifest, deck / "manifest.json")
    print(f"deck: {deck}\nphrases: {len(lines)}, failed: {failed}\nanki: {deck / 'anki.tsv'}")
    print("Импорт в Anki: файл anki.tsv + скопировать mp3 в collection.media")
    return 1 if failed else 0


async def cmd_dialog(args) -> int:
    deck = args.out / args.deck
    deck.mkdir(parents=True, exist_ok=True)
    replicas = parse_dialog(read_lines(Path(args.file)))
    cast = parse_cast(args.cast) if args.cast else {}
    cycle = [v.strip() for v in args.voices.split(",")]
    items = assign_voices(replicas, cycle, cast, args.narrator)
    jobs, manifest, tsv, parts = [], [], [], []
    for i, (speaker, text, voice) in enumerate(items, 1):
        label = f"{speaker}-{text}" if speaker else text
        normal = deck / f"{i:03d}-{slugify(label)}.mp3"
        srt = deck / f"{i:03d}-{slugify(label)}.srt"
        jobs.append(synth(text, voice, normal, srt, "+0%", args.volume, args.pitch, args.proxy))
        parts.append(normal)
        manifest.append({"file": normal.name, "speaker": speaker, "text": text, "voice": voice})
        who = f"[{speaker}] " if speaker else ""
        tsv.append(f"{who}{text} [sound:{normal.name}]")
    results = await run_jobs(jobs, args.jobs)
    failed = sum(1 for r in results if isinstance(r, Exception))
    write_playlist(parts, deck / "playlist.m3u")
    (deck / "anki.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    write_manifest(manifest, deck / "manifest.json")
    print(f"deck: {deck}\nreplicas: {len(items)}, failed: {failed}")
    if not args.no_mix and not failed:
        if have_ffmpeg():
            mix = deck / "mix.mp3"
            ffmpeg_concat(parts, mix, gap=args.gap)
            print(f"mix: {mix}  (весь диалог одним файлом, паузы {args.gap}с)")
        else:
            print("WARN: нет ffmpeg — mix пропущен, слушай по playlist.m3u")
    return 1 if failed else 0


async def cmd_cards(args) -> int:
    deck = args.out / args.deck
    deck.mkdir(parents=True, exist_ok=True)
    lines = read_lines(Path(args.file))
    jobs, tsv = [], []
    for i, line in enumerate(lines, 1):
        front, back = split_card(line)
        if not back:
            raise ValueError(f"Строка {i} без перевода — карточке нужен таб: фраза\\tперевод")
        f_mp3 = deck / f"{i:03d}-{slugify(front)}.mp3"
        jobs.append(synth(front, args.voice, f_mp3, None, "+0%", args.volume, args.pitch, args.proxy))
        front_cell = f"{front} [sound:{f_mp3.name}]"
        if args.back_voice:
            b_mp3 = deck / f"{i:03d}-{slugify(front)}@ru.mp3"
            jobs.append(synth(back, args.back_voice, b_mp3, None, "+0%", args.volume, args.pitch, args.proxy))
            back_cell = f"{back} [sound:{b_mp3.name}]"
        else:
            back_cell = back
        tsv.append(f"{front_cell}\t{back_cell}")
    results = await run_jobs(jobs, args.jobs)
    failed = sum(1 for r in results if isinstance(r, Exception))
    (deck / "anki.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    print(f"deck: {deck}\ncards: {len(lines)}, failed: {failed}\nanki: {deck / 'anki.tsv'}")
    return 1 if failed else 0


async def cmd_voices(args) -> int:
    if not args.live:
        for name in sorted(PRESETS):
            if not args.lang or PRESETS[name].startswith(args.lang):
                print(f"{name:10s} {PRESETS[name]}")
        print("\nЖивой список: voices --live [--lang de-DE]")
        return 0
    voices = await edge_tts.list_voices(proxy=args.proxy)
    for v in sorted(voices, key=lambda x: x["ShortName"]):
        if args.lang and not v["ShortName"].startswith(args.lang):
            continue
        print(f"{v['ShortName']:45s} {v['Gender']}")
    return 0


def cmd_selfcheck(_args) -> int:
    assert slugify("Guten Morgen, Welt!") == "guten-morgen-welt", slugify("Guten Morgen, Welt!")
    assert slugify("Grüße aus Köln") == "grusse-aus-koln", slugify("Grüße aus Köln")
    assert slugify("!!!") == "line"
    assert resolve_voice("de-f") == "de-DE-KatjaNeural"
    assert resolve_voice("en-GB-SoniaNeural") == "en-GB-SoniaNeural"
    for bad in ("de-x", "Katja", ""):
        try:
            resolve_voice(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"resolve_voice({bad!r}) должен падать")
    assert check_rate("-30%") == "-30%"
    try:
        check_rate("30")
    except ValueError:
        pass
    else:
        raise AssertionError("check_rate('30') должен падать")
    assert parse_cast("Анна=de-f,Бен=de-m") == {"Анна": "de-f", "Бен": "de-m"}
    assert parse_dialog(["Анна: Привет!", "Пауза."]) == [("Анна", "Привет!"), ("", "Пауза.")]
    items = assign_voices([("Анна", "A"), ("Бен", "B"), ("", "C"), ("Анна", "D")],
                          ["de-f", "de-m"], {}, "de-f")
    assert [v for _, _, v in items] == ["de-f", "de-m", "de-f", "de-f"], items
    print("selfcheck: OK (9 групп asserts)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--volume", default="+0%", help="Громкость, напр. +10%% (default: +0%%)")
    common.add_argument("--pitch", default="+0Hz", help="Тон, напр. -10Hz (default: +0Hz)")
    common.add_argument("--proxy", default=None, help="Прокси для движка, если прямой доступ режут")
    common.add_argument("--jobs", type=int, default=4, help="Параллельных запросов (default: 4)")
    common.add_argument("--out", type=Path, default=Path("out"), help="Куда класть результат (default: out/)")

    p = argparse.ArgumentParser(prog="voicedeck", description="Озвучка учебных текстов EN/DE")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("say", parents=[common], help="Одна фраза")
    s.add_argument("text", help="Текст для озвучки")
    s.add_argument("--voice", default="de-f", help="Пресет или полное имя (default: de-f)")
    s.add_argument("--slow-rate", default="-30%", help="Темп slow-версии (default: -30%%)")
    s.add_argument("--no-sub", action="store_true", help="Без субтитров")
    s.add_argument("--no-shadow", action="store_true", help="Без shadow-микса")
    s.add_argument("--gap", type=float, default=1.0, help="Пауза в shadow-миксе, сек (default: 1.0)")

    b = sub.add_parser("batch", parents=[common], help="Файл с фразами (фраза [\\tперевод])")
    b.add_argument("file", help="txt: по фразе на строку")
    b.add_argument("--voice", default="en-us-f", help="Голос пачки (default: en-us-f)")
    b.add_argument("--deck", default="deck", help="Имя папки в out/ (default: deck)")
    b.add_argument("--slow-rate", default="-30%")
    b.add_argument("--no-slow", action="store_true", help="Только normal, без slow")

    d = sub.add_parser("dialog", parents=[common], help="Диалог 'Имя: реплика'")
    d.add_argument("file", help="txt диалога")
    d.add_argument("--voices", default="de-f,de-m", help="Голоса по кругу (default: de-f,de-m)")
    d.add_argument("--cast", default="", help="Точный каст: Анна=de-f,Бен=de-m")
    d.add_argument("--narrator", default="de-f", help="Голос ремарок без имени (default: de-f)")
    d.add_argument("--deck", default="dialog", help="Имя папки в out/ (default: dialog)")
    d.add_argument("--gap", type=float, default=0.8, help="Пауза между репликами в mix, сек")
    d.add_argument("--no-mix", action="store_true", help="Без склейки mix.mp3")

    c = sub.add_parser("cards", parents=[common], help="TSV 'фраза\\tперевод' -> карточки Anki")
    c.add_argument("file", help="tsv карточек")
    c.add_argument("--voice", default="en-gb-f", help="Голос лицевой стороны (default: en-gb-f)")
    c.add_argument("--back-voice", default=None, help="Голос оборота, напр. ru-f (default: без озвучки)")
    c.add_argument("--deck", default="cards", help="Имя папки в out/ (default: cards)")

    v = sub.add_parser("voices", parents=[common], help="Голоса")
    v.add_argument("--live", action="store_true", help="Живой список с сервера")
    v.add_argument("--lang", default="", help="Фильтр, напр. de-DE или en-GB")

    sub.add_parser("selfcheck", help="Проверки без сети")
    return p


async def amain(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for key in ("slow_rate",):
        if hasattr(args, key):
            try:
                check_rate(getattr(args, key))
            except ValueError as e:
                print(f"ERROR: {e}")
                return 2
    if hasattr(args, "pitch"):
        try:
            check_pitch(args.pitch)
        except ValueError as e:
            print(f"ERROR: {e}")
            return 2
    try:
        if args.cmd == "say":
            return await cmd_say(args)
        if args.cmd == "batch":
            return await cmd_batch(args)
        if args.cmd == "dialog":
            return await cmd_dialog(args)
        if args.cmd == "cards":
            return await cmd_cards(args)
        if args.cmd == "voices":
            return await cmd_voices(args)
        if args.cmd == "selfcheck":
            return cmd_selfcheck(args)
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}")
        return 2
    except Exception as e:  # сеть/движок: не валим пачку целиком без диагноза
        print(f"ERROR: {type(e).__name__}: {e}")
        return 1
    raise AssertionError("unreachable")


def main() -> None:
    raise SystemExit(asyncio.run(amain()))


if __name__ == "__main__":
    main()
