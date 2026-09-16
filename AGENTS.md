# VoiceDeck — Instructions for AI Agents

## Commands
- install: `pip install edge-tts`
- selfcheck: `python scripts/voicedeck.py selfcheck` (проверки без сети)
- voices: `python scripts/voicedeck.py voices [--live] [--lang de-DE]`
- say: `python scripts/voicedeck.py say "<text>" --voice <preset>`
- batch: `python scripts/voicedeck.py batch phrases.txt --voice en-us-f --deck unit1`
- dialog: `python scripts/voicedeck.py dialog dialog.txt --cast "Anna=de-f,Ben=de-m"`
- cards: `python scripts/voicedeck.py cards cards.tsv --voice en-gb-f --back-voice ru-f`
- web: `python scripts/app.py [--port 8765]` (интерфейс учёбы) или `VoiceDeck.bat`
- web files: `scripts/app.py` (сервер, только stdlib) + `scripts/web/index.html` (vanilla, без CDN)
- python: `python` (3.13 по факту окружения), не `python3`
- test/lint/build: selfcheck вместо тестов; фреймворков нет

## Conventions
- Коммиты прямо в `main`, без веток и PR. Сообщение — повелительное наклонение, ≤ 72 символов, русский или английский
- Скрипты генерации — только в `scripts/`, не раскидывать по временным каталогам
- Сгенерированное аудио — в `out/` (не коммитить), исходные фразы — рядом со скриптом или в `inbox/`
- Язык общения: русский, технические термины — как есть (EN)

## Structure
- `scripts/` — CLI (voicedeck.py), веб-сервер (app.py), страница (web/index.html)
- `VoiceDeck.bat` — запуск интерфейса в один клик (Windows)
- `library/<lang>/<date>-<slug>/` — юниты: meta.json, story.txt, dialog.txt,
  phrases.txt (ядро, фраза<TAB>перевод), cards.tsv, audio/ (коммитится), anki.tsv
- `library/_template/` — шаблоны юнита; `library/en|de/` — треки
- meta.json: lang, level, date, topic, track, kind, voices{front,back},
  phrases (число), spiral_from (повторы из прошлых юнитов), source
- `out/` — сгенерированные mp3 (игнорируется git)
- `docs/` — только CONTEXT.md и DECISIONS.md

## Do NOT touch
- `.git/` руками не трогать, никакого `push --force` и `reset --hard` без подтверждения
- Не коммитить `out/`, `venv/`, `__pycache__/`
- Не создавать новых `.md` файлов без явного разрешения

## Documentation rules
- Перед работой — прочитай этот файл и контекст проекта
- После работы — обнови контекст проекта (статус, open-проблемы, журнал)
- Архитектурное решение — добавь в решения (append-only)
- Переиспользуемые знания — в базу знаний (`D:\GitHub\knowledge`)
