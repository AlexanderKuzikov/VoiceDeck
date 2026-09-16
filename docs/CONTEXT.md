# VoiceDeck — CONTEXT

> Последнее обновление: 2026-09-16 08:00

## Статус
| Компонент | Статус | Версия/Заметка |
|-----------|--------|----------------|
| Документация | done | README, AGENTS, CONTEXT, DECISIONS, MIT |
| Движок | done | edge-tts, живой прогон из РФ без VPN |
| CLI | done | say/batch/dialog/cards/voices/selfcheck |
| Эталонные голоса | done | Jenny/Sonia + Katja/Conrad по умолчанию |
| Smoke-набор | done | out/smoke: фраза, пачка, диалог, карточки |

## Open-проблемы
| # | Priority | Описание |
|---|----------|----------|
| 1 | medium | Вживую прослушать эталоны и подтвердить голоса под свой слух |

## Журнал работ
| Дата | Изменение |
|------|-----------|
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
