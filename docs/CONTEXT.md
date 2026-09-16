# VoiceDeck — CONTEXT

> Последнее обновление: 2026-09-16 07:30

## Статус
| Компонент | Статус | Версия/Заметка |
|-----------|--------|----------------|
| Документация | done | README, AGENTS, CONTEXT, DECISIONS |
| Движок | decided | Microsoft Neural через edge-tts, облако |
| Эталонные голоса | open | прослушать Jenny/Sonia + Katja/Conrad/Seraphina |
| Скрипты | todo | say.py, batch, диалоги |
| Формат выхода | open | mp3 в папку vs CSV под Anki |

## Open-проблемы
| # | Priority | Описание |
|---|----------|----------|
| 1 | high | Прослушать и зафиксировать эталонные голоса EN и DE |
| 2 | high | Решить: edge-tts free как база vs Azure Speech HD с ключом |
| 3 | medium | Формат выхода: просто mp3 или сразу сборка под Anki |
| 4 | low | Выбрать лицензию |

## Журнал работ
| Дата | Изменение |
|------|-----------|
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
