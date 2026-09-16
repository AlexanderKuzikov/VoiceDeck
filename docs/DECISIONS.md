# VoiceDeck — DECISIONS

<!-- Append-only. Формат фиксирован. -->

## 2026-09-16: Движок — Microsoft Neural через edge-tts, облако

**Контекст:** Нужна озвучка небольших текстов EN/DE уровня «живой голос, никаких роботов». Локальные движки отпали по качеству, Google AI Studio — по глюкам доступа из РФ, ElevenLabs — официально блочит Россию.

**Решение:** База — Microsoft Neural через бесплатный endpoint (либа edge-tts). Своё железо не участвует, VPN и ключи не нужны.

**Альтернативы:** ElevenLabs v3 (эталон выразительности, но бан РФ + VPN + иностранная карта); Gemini TTS (топ-качество, но suspicious-activity баны); Yandex SpeechKit (по одному голосу на EN/DE — мало); Piper/RHVoice локально (роботизированность).

**Trade-off:** Нет студийного HD-качества и эмоций уровня Eleven; неофициальное API без SLA — Microsoft может поменять endpoint.
