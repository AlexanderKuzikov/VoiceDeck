<p align="center">
  <a href="#"><img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
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
python scripts/voicedeck.py say "Guten Morgen!" --voice de-f
python scripts/voicedeck.py batch phrases.txt --voice en-us-f --deck unit1
python scripts/voicedeck.py dialog dialog.txt --cast "Anna=de-f,Ben=de-m"
python scripts/voicedeck.py cards cards.tsv --voice en-gb-f --back-voice ru-f
```

## Документация

- [Контекст проекта](docs/CONTEXT.md) — состояние проекта
- [Архитектурные решения](docs/DECISIONS.md) — архитектурные решения

## Статус

**v0.1.0** — CLI работает: фраза, пачка, диалог, карточки. Проверено живым прогоном.

## Лицензия

[MIT](LICENSE) © Alexander Kuzikov
