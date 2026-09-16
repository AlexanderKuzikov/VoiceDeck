<p align="center">
  <a href="#"><img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white"></a>
  <a href="#"><img alt="License" src="https://img.shields.io/badge/License-TBD-lightgrey.svg"></a>
</p>

<h1 align="center">VoiceDeck</h1>
<p align="center">Озвучка небольших текстов для изучения английского и немецкого на нейроголосах Microsoft</p>

---

Вставляешь фразу или диалог — получаешь mp3 в обычном и замедленном темпе для повторения и shadowing. Движок — облачный Microsoft Neural (те же голоса, что в Edge Read Aloud), своё железо не участвует.

- **Живые голоса** — Jenny/Sonia для английского, Katja/Conrad для немецкого, без роботов
- **Slow-версии** — замедление самим движком для разбора произношения
- **Диалоги** — склейка реплик двумя голосами в один файл
- **Без VPN и ключей** — бесплатный endpoint, работает из РФ

## Быстрый старт

```bash
git clone https://github.com/AlexanderKuzikov/VoiceDeck.git
cd VoiceDeck
pip install edge-tts
python scripts/say.py --voice de-DE-KatjaNeural --text "Guten Morgen!"
```

## Документация

- [Контекст проекта](docs/CONTEXT.md) — состояние проекта
- [Архитектурные решения](docs/DECISIONS.md) — архитектурные решения

## Статус

**v0.1.0** — Каркас и документация, скриптов пока нет.

## Лицензия

Не выбрана — см. open-проблемы в контексте проекта.
