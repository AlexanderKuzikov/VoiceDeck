#!/usr/bin/env python3
"""VoiceDeck Web — локальный интерфейс для учёбы.

    python scripts/app.py [--port 8765] [--no-browser]

Открывает страницу в браузере: фраза, пачка, диалог, карточки.
Зависимости сверх voicedeck.py: только стандартная библиотека.
"""

import argparse
import asyncio
import hashlib
import io
import json
import re
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from voicedeck import (
    PRESETS, assign_voices, ffmpeg_concat, have_ffmpeg,
    parse_cast, parse_dialog, run_jobs, slugify, split_card, synth,
    write_manifest,
)

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "out" / "web"
INDEX = Path(__file__).resolve().parent / "web" / "index.html"
MAX_BODY = 512 * 1024

GROUPS = {"en": "Английский", "de": "Немецкий", "ru": "Русский"}

SRT_TS = re.compile(r"(\d+):(\d+):([\d.,]+)\s*-->\s*(\d+):(\d+):([\d.,]+)")


def key(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]


def ts_to_sec(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))


def srt_words(srt: str) -> list[dict]:
    """Субтитры -> слова с таймингами для подсветки при чтении."""
    words: list[dict] = []
    for block in srt.strip().split("\n\n"):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 3:
            continue
        m = SRT_TS.search(lines[1])
        if not m:
            continue
        t0 = ts_to_sec(*m.groups()[:3])
        t1 = ts_to_sec(*m.groups()[3:])
        text = " ".join(lines[2:])
        n = len(text.split())
        if not n:
            continue
        step = (t1 - t0) / n
        for i, w in enumerate(text.split()):
            words.append({"w": w, "t0": round(t0 + step * i, 3), "t1": round(t0 + step * (i + 1), 3)})
    return words


def unique_dir(base: str) -> Path:
    stem = slugify(base) or "deck"
    dest = WEB / stem
    n = 2
    while dest.exists():
        dest = WEB / f"{stem}-{n}"
        n += 1
    dest.mkdir(parents=True)
    return dest


class Handler(BaseHTTPRequestHandler):
    server_version = "VoiceDeck/0.2"

    def log_message(self, *args):  # тихий лог
        pass

    # --- helpers ---

    def send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("Слишком большой запрос")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def audio_url(self, path: Path) -> str:
        return "/audio/" + path.name

    # --- GET ---

    def do_GET(self) -> None:
        url = urlparse(self.path)
        try:
            if url.path == "/":
                self.serve_file(INDEX, "text/html; charset=utf-8")
            elif url.path == "/api/voices":
                self.send_json({"voices": [
                    {"id": vid, "voice": v, "group": GROUPS.get(vid.split("-")[0], "?"),
                     "label": f"{v.replace('Neural', '')} · {vid}"}
                    for vid, v in sorted(PRESETS.items())
                ]})
            elif url.path == "/api/zip":
                self.serve_zip(parse_qs(url.query).get("dir", [""])[0])
            elif url.path.startswith("/audio/"):
                rel = url.path[len("/audio/"):]
                if not rel or ".." in rel:
                    self.send_json({"error": "Нет такого файла"}, 404)
                    return
                target = (WEB / rel).resolve()
                if not str(target).startswith(str(WEB.resolve())) or not target.is_file():
                    self.send_json({"error": "Нет такого файла"}, 404)
                    return
                ctype = "audio/mpeg" if target.suffix == ".mp3" else "application/octet-stream"
                if target.suffix == ".tsv":
                    ctype = "text/tab-separated-values; charset=utf-8"
                elif target.suffix == ".m3u":
                    ctype = "audio/x-mpegurl; charset=utf-8"
                self.serve_file(target, ctype, download=target.suffix in (".tsv",))
            else:
                self.send_json({"error": "Неизвестный путь"}, 404)
        except Exception as e:  # сеть/файлы: отдать диагноз, не молчать
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def serve_file(self, path: Path, ctype: str, download: bool = False) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if download:
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{path.name}")
        self.end_headers()
        self.wfile.write(body)

    def serve_zip(self, dirname: str) -> None:
        if not dirname or "/" in dirname or "\\" in dirname:
            self.send_json({"error": "Плохое имя папки"}, 400)
            return
        target = (WEB / dirname).resolve()
        if not str(target).startswith(str(WEB.resolve())) or not target.is_dir():
            self.send_json({"error": "Нет такой папки"}, 404)
            return
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(target.iterdir()):
                if f.is_file():
                    zf.write(f, f.name)
        body = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{dirname}.zip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --- POST ---

    def do_POST(self) -> None:
        try:
            data = self.read_json()
            if self.path == "/api/synth":
                self.send_json(asyncio.run(api_synth(data)))
            elif self.path == "/api/batch":
                self.send_json(asyncio.run(api_batch(data)))
            elif self.path == "/api/dialog":
                self.send_json(asyncio.run(api_dialog(data)))
            elif self.path == "/api/cards":
                self.send_json(asyncio.run(api_cards(data)))
            else:
                self.send_json({"error": "Неизвестный путь"}, 404)
        except (ValueError, KeyError) as e:
            self.send_json({"error": str(e)}, 400)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)


async def api_synth(d: dict) -> dict:
    text = (d.get("text") or "").strip()
    if not text:
        raise ValueError("Пустой текст")
    voice = d.get("voice") or "de-f"
    slow_rate = d.get("slowRate") or "-30%"
    gap = float(d.get("gap") or 1.0)
    tag = key(text, voice, slow_rate)
    slug = slugify(text)
    normal = WEB / f"p-{tag}-{slug}.mp3"
    srt = WEB / f"p-{tag}-{slug}.srt"
    jobs = [synth(text, voice, normal, srt)]
    slow = None
    if d.get("slow", True):
        slow = WEB / f"p-{tag}-{slug}@slow.mp3"
        jobs.append(synth(text, voice, slow, None, rate=slow_rate))
    await run_jobs(jobs, 4)
    out = {"normal": "/audio/" + normal.name,
           "slow": "/audio/" + slow.name if slow else None,
           "words": srt_words(srt.read_text(encoding="utf-8"))}
    if d.get("shadow") and slow and have_ffmpeg():
        shadow = WEB / f"p-{tag}-{slug}@shadow.mp3"
        ffmpeg_concat([slow, normal], shadow, gap=gap)
        out["shadow"] = "/audio/" + shadow.name
    return out


def non_empty_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in (text or "").splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("#")]
    if not lines:
        raise ValueError("Нет строк для озвучки")
    return lines


async def api_batch(d: dict) -> dict:
    lines = non_empty_lines(d.get("text", ""))
    deck = unique_dir(d.get("deck") or "pack")
    voice = d.get("voice") or "en-us-f"
    slow_rate = d.get("slowRate") or "-30%"
    want_slow = d.get("slow", True)
    jobs, rows, manifest, tsv = [], [], [], []
    for i, line in enumerate(lines, 1):
        phrase, trans = split_card(line)
        base = f"{i:03d}-{slugify(phrase)}"
        normal, srt = deck / f"{base}.mp3", deck / f"{base}.srt"
        jobs.append(synth(phrase, voice, normal, srt))
        row = {"text": phrase, "trans": trans,
               "audio": f"/audio/{deck.name}/{normal.name}", "slow": None}
        slow_name = None
        if want_slow:
            slow = deck / f"{base}@slow.mp3"
            jobs.append(synth(phrase, voice, slow, None, rate=slow_rate))
            slow_name = slow.name
            row["slow"] = f"/audio/{deck.name}/{slow.name}"
        rows.append(row)
        manifest.append({"file": normal.name, "slow": slow_name, "text": phrase,
                         "trans": trans, "voice": voice, "rate": "+0%"})
        cell = f"{phrase} [sound:{normal.name}]"
        tsv.append(f"{cell}\t{trans}" if trans else cell)
    failed = sum(1 for r in await run_jobs(jobs, 4) if isinstance(r, Exception))
    (deck / "anki.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    write_manifest(manifest, deck / "manifest.json")
    return {"dir": deck.name, "rows": rows, "failed": failed,
            "tsv": "/audio/" + deck.name + "/anki.tsv", "zip": "/api/zip?dir=" + deck.name}


async def api_dialog(d: dict) -> dict:
    replicas = parse_dialog(non_empty_lines(d.get("text", "")))
    cast = parse_cast(d["cast"]) if d.get("cast") else {}
    cycle = [v.strip() for v in (d.get("voices") or "de-f,de-m").split(",")]
    items = assign_voices(replicas, cycle, cast, d.get("narrator") or "de-f")
    deck = unique_dir(d.get("deck") or "dialog")
    gap = float(d.get("gap") or 0.8)
    jobs, lines, parts, tsv, manifest = [], [], [], [], []
    for i, (speaker, text, voice) in enumerate(items, 1):
        base = f"{i:03d}-{slugify((speaker + '-' + text) if speaker else text)}"
        mp3, srt = deck / f"{base}.mp3", deck / f"{base}.srt"
        jobs.append(synth(text, voice, mp3, srt))
        parts.append(mp3)
        lines.append({"speaker": speaker, "text": text, "audio": f"/audio/{deck.name}/{mp3.name}"})
        manifest.append({"file": mp3.name, "speaker": speaker, "text": text, "voice": voice})
        who = f"[{speaker}] " if speaker else ""
        tsv.append(f"{who}{text} [sound:{mp3.name}]")
    failed = sum(1 for r in await run_jobs(jobs, 4) if isinstance(r, Exception))
    (deck / "anki.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    (deck / "playlist.m3u").write_text("#EXTM3U\n" + "\n".join(p.name for p in parts) + "\n", encoding="utf-8")
    write_manifest(manifest, deck / "manifest.json")
    mix = None
    if d.get("mix", True) and not failed and have_ffmpeg():
        mp = deck / "mix.mp3"
        ffmpeg_concat(parts, mp, gap=gap)
        mix = f"/audio/{deck.name}/mix.mp3"
    return {"dir": deck.name, "lines": lines, "mix": mix, "failed": failed,
            "tsv": "/audio/" + deck.name + "/anki.tsv", "zip": "/api/zip?dir=" + deck.name}


async def api_cards(d: dict) -> dict:
    lines = non_empty_lines(d.get("text", ""))
    deck = unique_dir(d.get("deck") or "cards")
    voice, back_voice = d.get("voice") or "en-gb-f", d.get("backVoice")
    jobs, cards, tsv = [], [], []
    for i, line in enumerate(lines, 1):
        front, back = split_card(line)
        if not back:
            raise ValueError(f"Строка {i} без перевода — нужен таб: фраза\\tперевод")
        f_mp3 = deck / f"{i:03d}-{slugify(front)}.mp3"
        jobs.append(synth(front, voice, f_mp3))
        front_cell = f"{front} [sound:{f_mp3.name}]"
        back_cell = back
        back_url = None
        if back_voice:
            b_mp3 = deck / f"{i:03d}-{slugify(front)}@ru.mp3"
            jobs.append(synth(back, back_voice, b_mp3))
            back_cell = f"{back} [sound:{b_mp3.name}]"
            back_url = f"/audio/{deck.name}/{b_mp3.name}"
        cards.append({"front": front, "back": back,
                      "frontAudio": f"/audio/{deck.name}/{f_mp3.name}", "backAudio": back_url})
        tsv.append(f"{front_cell}\t{back_cell}")
    failed = sum(1 for r in await run_jobs(jobs, 4) if isinstance(r, Exception))
    (deck / "anki.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    return {"dir": deck.name, "cards": cards, "failed": failed,
            "tsv": "/audio/" + deck.name + "/anki.tsv", "zip": "/api/zip?dir=" + deck.name}


def main() -> None:
    ap = argparse.ArgumentParser(description="VoiceDeck Web — интерфейс учёбы")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    WEB.mkdir(parents=True, exist_ok=True)
    if not INDEX.is_file():
        raise SystemExit(f"Нет {INDEX}")
    port = args.port
    for _ in range(10):
        try:
            server = ThreadingHTTPServer((args.host, port), Handler)
            break
        except OSError:
            port += 1
    else:
        raise SystemExit("Нет свободного порта рядом с " + str(args.port))
    url = f"http://{args.host}:{port}/"
    print(f"VoiceDeck: {url}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлен")


if __name__ == "__main__":
    main()
