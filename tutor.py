import speech_recognition as sr
import ollama
from faster_whisper import WhisperModel
import os
import sys
import traceback
import shutil
import zipfile
import urllib.request
import datetime
import re

# Add current directory to PATH so pydub/RealtimeTTS can find ffmpeg.exe
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration
MODEL_NAME = "llama3"  # Ensure you have run 'ollama pull llama3' previously, previus model
MODEL_NAME = "gemma4:e2b" # This is the only model I could use from Gemma new models.Other models are too much for current setting. 
WHISPER_SIZE = "base.en"  # Use "small.en" for better accuracy at the cost of speed

# Condensed CV context injected into system prompts
CV_CONTEXT = (
    "The student is Juan Carlos, a Data Scientist with 6+ years of experience based in Ecuador. "
    "Background: ML and statistics, primarily in the financial and public sectors. "
    "Key tools: Python (Pandas, Scikit-learn, PyTorch, XGBoost), PySpark, Azure Databricks, SQL, Hugging Face, R. "
    "Recent roles: Consultant at CGESPLAN (2026-present), Credit Risk Specialist at BIESS (2025-2026), "
    "Data Scientist at Banco Pichincha (2019-2024). "
    "Also experienced in public-sector analytics: INEC, Bloomberg Philanthropies, SENPLADES, OIT. "
    "Education: Master of Economics (University of Queensland, Australia). "
    "English level: advanced non-native speaker. Native language: Spanish. "
    "Goal: prepare for technical job interviews conducted in English."
)

INTERVIEW_SYSTEM_PROMPT = (
    "You are a professional English-language technical interview coach.\n"
    f"{CV_CONTEXT}\n\n"
    "You are in INTERVIEW MODE.\n"
    "1. Ask one interview question at a time, relevant to the student's background.\n"
    "2. After the student answers:\n"
    "   a. Briefly note any English grammar or phrasing issues, gently.\n"
    "   b. Give brief feedback on whether the answer addresses the question well.\n"
    "   c. End your reply with exactly: 'Say \"next\" when you are ready for the next question.'\n"
    "3. IMPORTANT: Do NOT ask the next question after giving feedback. Always stop and wait.\n"
    "   Only ask the next question when the student explicitly says they are ready.\n"
    "Keep all responses concise. Vary questions across: behavioral (STAR format), ML concepts, Python, "
    "and statistics/econometrics.\n"
    "Begin by asking the first question now."
)

CONVERSATION_SYSTEM_PROMPT = (
    "You are a friendly and helpful English tutor.\n"
    f"{CV_CONTEXT}\n\n"
    "You are in CONVERSATION MODE. Have a free-form conversation with the student.\n"
    "If the student makes a grammar mistake, gently correct them before replying.\n"
    "Keep your answers concise. Feel free to bring up topics related to the student's professional background."
)

print("Initializing the Digital Tutor...")

# Check for FFmpeg (required by RealtimeTTS/pydub)
def is_installed(lib_name):
    return shutil.which(lib_name) or os.path.isfile(lib_name + ".exe") or os.path.isfile(lib_name)

if not is_installed("ffmpeg") or not is_installed("ffprobe"):
    print("FFmpeg not found. Downloading automatically (this may take a minute)...")
    print("Tip: place ffmpeg.exe and ffprobe.exe in this folder to skip this step in the future.")
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg.zip"
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("Extracting FFmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith("bin/ffmpeg.exe"):
                    with zip_ref.open(file) as source, open(os.path.join(script_dir, "ffmpeg.exe"), "wb") as target:
                        shutil.copyfileobj(source, target)
                elif file.endswith("bin/ffprobe.exe"):
                    with zip_ref.open(file) as source, open(os.path.join(script_dir, "ffprobe.exe"), "wb") as target:
                        shutil.copyfileobj(source, target)
        print("FFmpeg installed successfully!")
        if os.path.exists(zip_path):
            os.remove(zip_path)
    except Exception as e:
        print(f"\nCRITICAL ERROR: Failed to download FFmpeg: {e}")
        sys.exit(1)

os.environ["PATH"] += os.pathsep + script_dir

# Import RealtimeTTS after FFmpeg is confirmed present
try:
    from RealtimeTTS import TextToAudioStream, SystemEngine
except ImportError:
    print("Error importing RealtimeTTS. Make sure requirements are installed.")
    sys.exit(1)

# Check Ollama connection
print("Checking Ollama connection...")
try:
    ollama.list()
except Exception as e:
    print("\nCRITICAL ERROR: Cannot connect to Ollama!")
    print("Please ensure the Ollama application is running in your system tray.")
    print(f"Details: {e}\n")
    sys.exit(1)

# Setup Whisper (Ear)
print("Loading Whisper model (this might take a moment)...")
whisper_model = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8")

# Setup TTS (Mouth)
print("Initializing TTS...")
engine = SystemEngine()
stream = TextToAudioStream(engine)

# Setup recorder
recognizer = sr.Recognizer()
recognizer.pause_threshold = 2.5  # seconds of silence before a phrase is considered finished


def clean_for_speech(text):
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)   # ## headers
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)  # --- separators
    text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)       # **bold** / *italic*
    text = re.sub(r'_{1,2}([^_]+?)_{1,2}', r'\1', text)          # __bold__ / _italic_
    text = re.sub(r'`([^`]+?)`', r'\1', text)                     # `inline code`
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)          # [link](url)
    text = re.sub(r'[*_`|\\]', '', text)                          # leftover symbols
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def select_mode():
    print("\n--- Mode Selection ---")
    print("1. Interview Mode     — technical interview practice with feedback")
    print("2. Conversation Mode  — free-form grammar-corrected chat")
    while True:
        choice = input("Select mode (1 or 2): ").strip()
        if choice == "1":
            return "interview", INTERVIEW_SYSTEM_PROMPT
        elif choice == "2":
            return "conversation", CONVERSATION_SYSTEM_PROMPT
        else:
            print("Please enter 1 or 2.")


def setup_log(mode_name):
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(logs_dir, f"session_{mode_name}_{timestamp}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Session: {mode_name.upper()} | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 60 + "\n")
    return path


def log_turn(log_path, speaker, text):
    with open(log_path, "a", encoding="utf-8") as f:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        f.write(f"[{ts}] {speaker}: {text}\n")


def record_audio(filename="input.wav"):
    with sr.Microphone() as source:
        print("\nListening... (Speak now)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=90)
            with open(filename, "wb") as f:
                f.write(audio.get_wav_data())
            return True
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return False
        except Exception as e:
            print(f"Microphone error: {e}")
            return False


def transcribe_audio(filename="input.wav"):
    segments, _ = whisper_model.transcribe(filename, beam_size=5)
    return "".join([seg.text for seg in segments]).strip()


def chat_with_ollama(user_text, conversation_history):
    conversation_history.append({"role": "user", "content": user_text})
    response = ollama.chat(model=MODEL_NAME, messages=conversation_history)
    ai_text = response['message']['content']
    conversation_history.append({"role": "assistant", "content": ai_text})
    return ai_text


NEXT_TRIGGERS = {"next", "next question", "go ahead", "go on"}


def is_next_trigger(text):
    """Return True only when the entire utterance is an advancement command.

    Uses exact matching after normalising case and stripping trailing
    punctuation — so 'next.' matches but 'yes, next I want to explain...' does not.
    """
    cleaned = text.lower().strip().rstrip(".,!?")
    return cleaned in NEXT_TRIGGERS


def generate_summary(history, log_path):
    print("\nGenerating session summary...")
    summary_prompt = (
        "The session has ended. Based on our conversation, give a brief summary of the student's "
        "main areas for English improvement. Focus on recurring grammar patterns, vocabulary gaps, "
        "or phrasing issues that came up. Keep it concise and actionable — 3 to 5 bullet points."
    )
    response = ollama.chat(model=MODEL_NAME, messages=history + [{"role": "user", "content": summary_prompt}])
    summary_text = response['message']['content']
    print(f"\n--- Session Summary ---\n{summary_text}\n")
    log_turn(log_path, "Summary", summary_text)
    return summary_text


def main():
    mode_name, system_prompt = select_mode()
    log_path = setup_log(mode_name)
    print(f"\nSession log: {log_path}")

    history = [{"role": "system", "content": system_prompt}]

    print(f"\nTutor is ready in {mode_name.upper()} mode! Say 'Goodbye' to exit.")
    if mode_name == "interview":
        print("Tip: take as long as you need to answer. Say 'next' when you want the next question.\n")
    else:
        print()

    # In interview mode, the tutor opens with the first question immediately
    if mode_name == "interview":
        print("Thinking of first question...")
        first_question = chat_with_ollama("Let's begin.", history)
        print(f"Tutor: {first_question}")
        log_turn(log_path, "Tutor", first_question)
        stream.feed(clean_for_speech(first_question))
        stream.play()

    try:
        while True:
            try:
                if not record_audio():
                    continue

                print("Transcribing...")
                user_text = transcribe_audio()
                if not user_text:
                    continue
                print(f"You said: {user_text}")
                log_turn(log_path, "You", user_text)

                if any(w in user_text.lower() for w in ["goodbye", "good bye", "bye"]):
                    farewell = "Goodbye! Great session. Keep practicing!"
                    print(f"Tutor: {farewell}")
                    log_turn(log_path, "Tutor", farewell)
                    stream.feed(clean_for_speech(farewell))
                    stream.play()
                    summary = generate_summary(history, log_path)
                    stream.feed(clean_for_speech(summary))
                    stream.play()
                    sys.exit(0)

                print("Thinking...")
                if mode_name == "interview" and is_next_trigger(user_text):
                    ai_response = chat_with_ollama(
                        "The student is ready. Please ask the next interview question.", history
                    )
                else:
                    ai_response = chat_with_ollama(user_text, history)
                print(f"Tutor: {ai_response}")
                log_turn(log_path, "Tutor", ai_response)
                stream.feed(clean_for_speech(ai_response))
                stream.play()

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                traceback.print_exc()
                print("Resuming listener...\n")
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
