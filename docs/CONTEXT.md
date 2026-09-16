# VoiceDeck — CONTEXT

> Последнее обновление: 2026-09-16 08:30

## Статус
| Компонент | Статус | Версия/Заметка |
|-----------|--------|----------------|
| Документация | done | README, AGENTS, CONTEXT, DECISIONS, MIT |
| Движок | done | edge-tts, живой прогон из РФ без VPN |
| CLI | done | say/batch/dialog/cards/voices/selfcheck |
| Web-интерфейс | done | 4 вкладки, тренажёр карточек, ZIP-пакеты; все ручки проверены |
| Библиотека | scaffold | library/_template + треки en/de, юнитов пока нет |
| Эталонные голоса | done | Jenny/Sonia + Katja/Conrad по умолчанию |
| Smoke-набор | done | out/smoke: фраза, пачка, диалог, карточки |

## Open-проблемы
| # | Priority | Описание |
|---|----------|----------|
| 1 | medium | Вживую прослушать эталоны и подтвердить голоса под свой слух |
| 2 | high | Day 1: EN-юнит B2 work (story + 10 фраз) |
| 3 | high | Day 1: DE-пак A1 (5 фраз, только словарный запас) |
| 4 | medium | Команда build: сборка юнита из txt в audio+anki одной командой |

## Журнал работ
| Дата | Изменение |
|------|-----------|
| 2026-09-16 | План Week 1 выдан (17–23.09): EN work-тред + DE словарь, день 7 — замер |
| 2026-09-16 | Каркас библиотеки: unit-шаблон, meta.json, треки en/de |
| 2026-09-16 | Фикс пустого списка голосов: синтаксическая ошибка в скрипте страницы, проверено в браузере end-to-end |
| 2026-09-16 | Web-интерфейс: 4 вкладки, тренажёр карточек, подсветка слов, ZIP; VoiceDeck.bat |
| 2026-09-16 | CLI voicedeck.py: say/batch/dialog/cards/voices/selfcheck + живой smoke-прогон |
| 2026-09-16 | Лицензия MIT |
| 2026-09-16 | Каркас проекта: документация, git, remote |

## Структура проекта
```
VoiceDeck/
├── README.md
├── AGENTS.md
├── .gitignore
├── scripts/        # CLI-автоматизация (todo)
├── out/            # сгенерированные mp3 (gitignore)
└── docs/
    ├── CONTEXT.md
    └── DECISIONS.md
```
