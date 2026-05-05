# Personal English Tutor

An offline, voice-based English tutor and technical interview coach powered by Ollama (LLaMA 3), Faster-Whisper, and RealtimeTTS.

## Prerequisites

1. **Ollama** — install the desktop app, then pull the model:
   ```bash
   ollama pull llama3
   ```
   This model bellow is the only that works for current setting, for further information on gamma4 implementation on models go to [ollama link](https://ollama.com/library/gemma4).
   ```bash
   ollama pull gemma4:e2b
   ```

   If you require to remove a model for some reason do:
   ```bash
   ollama remove llama3
   ```

   Keep the Ollama app running (system tray) whenever you use the tutor.

2. **FFmpeg** — place `ffmpeg.exe` and `ffprobe.exe` in the project folder to avoid an automatic download at first run. Download from: https://www.gyan.dev/ffmpeg/builds/ (grab the `release-essentials` zip, extract the `bin/` executables).

3. **Python 3.9+** with the virtual environment activated.

## Installation

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

## Running

```bash
python tutor.py
```

At startup you will be prompted to choose a mode:

| Mode | Description |
|---|---|
| **1 — Interview** | The tutor asks one technical question at a time. Answer at your own pace (up to 90 seconds per phrase). After your answer it gives brief feedback on your English and your content, then **waits**. Say **"next"** when you are ready to move on. |
| **2 — Conversation** | Free-form grammar-corrected chat on any topic. |

### Interview mode controls

| What to say | Effect |
|---|---|
| *(your answer)* | Tutor gives feedback and waits |
| `"next"` / `"next question"` / `"go ahead"` / `"go on"` | Tutor asks the next question |
| `"Goodbye"` | Ends the session |

## Session logs

Every session is saved to `logs/session_<mode>_<timestamp>.txt` for self-review after practice.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot connect to Ollama" | Open the Ollama desktop app (system tray icon) |
| Microphone not detected | Check Windows mic permissions; try `sr.Microphone(device_index=N)` with a different index |
| TTS is silent | Ensure a Windows SAPI voice is installed: Settings → Time & Language → Speech |
| FFmpeg missing error | Place `ffmpeg.exe` + `ffprobe.exe` in the project folder |
| Whisper is slow | Switch to `WHISPER_SIZE = "tiny.en"` in `tutor.py` for faster (less accurate) transcription |
