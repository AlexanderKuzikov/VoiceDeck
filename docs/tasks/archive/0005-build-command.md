# Задача 0005 — Команда build: сборка юнита одной командой

> Проект: VoiceDeck. Статус: принята. Дата: 2026-10-11.

## Задание

Добавить в CLI команду `build <unit-dir>`: читает meta.json + story.txt/phrases.txt/dialog.txt
(что есть), синтезирует всё в `audio/`, кладёт рядом anki.tsv. Закрывает open-проблему
про build. Прототипы сборок 0001/0002 — в песочнице штаба, перенести по-чистому.

Входит:
- `voicedeck.py build`: story (normal+slow+srt+shadow), phrases (normal+slow+srt),
  dialog (реплики + mix при ffmpeg), anki.tsv, голос из meta (перекрывается флагом)
- строка в AGENTS.md (Commands), selfcheck не ломать

Не входит: веб-кнопка сборки, матрица покрытия.

Старт: функции synth/run_jobs/ffmpeg_concat/slugify/parse_dialog уже в файле.

Приёмка:
- `python scripts/voicedeck.py selfcheck` — OK
- пересборка юнита Day 1 из чистого audio/ даёт те же имена файлов

Ограничения: один файл, без новых зависимостей; чужие треки не трогать.

## Порядок работы

Прочитай AGENTS.md и контекст → сделай → проверь по приёмке → допиши отчёт ниже → статус «на проверке», жди.

## Отчёт сессии

Штаб, 2026-10-11. Команда `build <unit-dir>` добавлена в voicedeck.py:
story (normal+slow+srt+shadow), phrases (normal+slow+srt), dialog (реплики+mix),
anki.tsv; голос/каст из meta.json с перекрытием флагами.
Приёмка: selfcheck OK; пересборка Day 1 из пустого audio/ — те же имена файлов,
0 ошибок. Статус: принята.
