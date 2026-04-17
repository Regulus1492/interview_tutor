# Digital English Tutor: Architecture Plan

## The Architecture: "Ear, Brain, and Mouth"

The system runs entirely offline on a Windows machine. Three components work in a Python loop:

1. **The Ear (STT):** `Faster-Whisper` — captures voice and converts it to text locally.
2. **The Brain (LLM):** `Ollama` (LLaMA 3) — receives text, reasons as a tutor, generates a response.
3. **The Mouth (TTS):** `RealtimeTTS` (SystemEngine) — reads the response back aloud.

**Privacy & Cost:** $0. All software and models are open source. No API keys. Voice data stays in RAM and is flushed when the script closes.

---

## Stack

| Component | Library | Notes |
|---|---|---|
| STT | `faster-whisper` (`base.en`) | CPU/INT8; switch to `small.en` for better accuracy |
| LLM | `ollama` + LLaMA 3 | Local inference via Ollama desktop app |
| TTS | `RealtimeTTS` (SystemEngine) | Windows SAPI; upgrade path: CoquiEngine |
| Audio capture | `SpeechRecognition` + `pyaudio` | Records to `.wav`, passed to Whisper |

---

## Implemented Features (Phase 1)

- [x] Voice capture → Whisper transcription → Ollama → TTS playback loop
- [x] CV-aware system prompt (Data Scientist background, financial/public sector, Ecuador)
- [x] Two modes selectable at startup:
  - **Interview mode** — tutor asks questions one at a time, evaluates English + content per answer
  - **Conversation mode** — free-form grammar-corrected chat
- [x] Session transcript log written to `logs/session_<mode>_<timestamp>.txt`
- [x] Graceful exit on "Goodbye"
- [x] FFmpeg auto-download fallback if not found locally

---

## Roadmap

### Medium-term

- [ ] **Difficulty dial** — prompt variable that shifts from "entry-level" to "senior" framing
- [ ] **Domain selection at startup** — behavioral, technical ML, Python coding, econometrics/stats
- [ ] **Upgrade TTS** — swap `SystemEngine` for `CoquiEngine` for natural intonation (one config line once Coqui is installed)

### Long-term / Parking Lot

- [ ] Structured scoring rubric per answer (content accuracy 1–5, fluency 1–5)
- [ ] Session analytics: track which domains the student struggles with over time
- [ ] Retrieval-augmented question bank: store past job descriptions and generate questions from them
- [ ] Voice cloning: record a custom "interviewer" voice profile using XTTS
