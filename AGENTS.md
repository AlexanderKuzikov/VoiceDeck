# VoiceDeck — Instructions for AI Agents

## Commands
- install: `pip install edge-tts`
- voices: `edge-tts --list-voices`
- say: `python scripts/say.py --voice <VoiceName> --text "<text>"`
- python: `python` (3.13 по факту окружения), не `python3`
- test/lint/build: пока нет, добавить при появлении кода

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
