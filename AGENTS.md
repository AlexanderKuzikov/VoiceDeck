# VoiceDeck — Instructions for AI Agents

## Commands
- install: `pip install edge-tts`
- selfcheck: `python scripts/voicedeck.py selfcheck` (проверки без сети)
- voices: `python scripts/voicedeck.py voices [--live] [--lang de-DE]`
- say: `python scripts/voicedeck.py say "<text>" --voice <preset>`
- batch: `python scripts/voicedeck.py batch phrases.txt --voice en-us-f --deck unit1`
- dialog: `python scripts/voicedeck.py dialog dialog.txt --cast "Anna=de-f,Ben=de-m"`
- cards: `python scripts/voicedeck.py cards cards.tsv --voice en-gb-f --back-voice ru-f`
- python: `python` (3.13 по факту окружения), не `python3`
- test/lint/build: selfcheck вместо тестов; фреймворков нет

## Conventions
- Коммиты прямо в `main`, без веток и PR. Сообщение — повелительное наклонение, ≤ 72 символов, русский или английский
- Скрипты генерации — только в `scripts/`, не раскидывать по временным каталогам
- Сгенерированное аудио — в `out/` (не коммитить), исходные фразы — рядом со скриптом или в `inbox/`
- Язык общения: русский, технические термины — как есть (EN)

## Structure
- `scripts/` — CLI-автоматизация (say, batch, диалоги)
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
