import speech_recognition as sr
import ollama
from faster_whisper import WhisperModel
import os
import sys
import traceback
import shutil
import zipfile
import urllib.request

# Add current directory to PATH so pydub/RealtimeTTS can find ffmpeg.exe if it is in this folder
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration
MODEL_NAME = "llama3"  # Ensure you have run 'ollama run llama3' in terminal previously
WHISPER_SIZE = "base.en" # "base.en" is fast and accurate for English. Use "small.en" for better accuracy.

print("Initializing the Digital Tutor...")

# Check for FFmpeg (Required for RealtimeTTS/pydub)
def is_installed(lib_name):
    return shutil.which(lib_name) or os.path.isfile(lib_name + ".exe") or os.path.isfile(lib_name)

if not is_installed("ffmpeg") or not is_installed("ffprobe"):
    print("FFmpeg not found. Downloading automatically (this may take a minute)...")
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

# Update PATH to include the current directory (where ffmpeg now is)
os.environ["PATH"] += os.pathsep + script_dir

# Import RealtimeTTS AFTER ensuring FFmpeg is present and in PATH
try:
    from RealtimeTTS import TextToAudioStream, SystemEngine
except ImportError:
    print("Error importing RealtimeTTS. Make sure requirements are installed.")
    sys.exit(1)

# Check for Ollama connection
print("Checking Ollama connection...")
try:
    ollama.list()
except Exception as e:
    print("\nCRITICAL ERROR: Cannot connect to Ollama!")
    print("Please ensure the Ollama application is running in your system tray.")
    print(f"Details: {e}\n")
    sys.exit(1)

# 1. Setup the Ear (Whisper)
print("Loading Whisper model (this might take a moment)...")
# Run on CPU with INT8 quantization for compatibility. 
# If you have a GPU, change device="cuda" and compute_type="float16".
whisper_model = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8")

# 2. Setup the Mouth (TTS)
print("Initializing TTS...")
# We use SystemEngine first because it's fast and reliable.
engine = SystemEngine() 
stream = TextToAudioStream(engine)

# 3. Setup the Recorder
recognizer = sr.Recognizer()

def record_audio(filename="input.wav"):
    with sr.Microphone() as source:
        print("\nListening... (Speak now)")
        # Adjust for background noise
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Listen until silence
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
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
    text = "".join([segment.text for segment in segments]).strip()
    return text

def chat_with_ollama(user_text, conversation_history):
    conversation_history.append({"role": "user", "content": user_text})
    
    response = ollama.chat(model=MODEL_NAME, messages=conversation_history)
    ai_text = response['message']['content']
    
    conversation_history.append({"role": "assistant", "content": ai_text})
    return ai_text

def main():
    # System Prompt: Defines the Tutor's personality
    history = [
        {"role": "system", "content": "You are a friendly and helpful English tutor. Your goal is to converse with the user. If the user makes a grammar mistake, gently correct them before replying to the content of their message. Keep your answers concise."}
    ]

    print("Tutor is ready! Say 'Goodbye' to exit.")

    try:
        while True:
            try:
                if not record_audio():
                    continue

                print("Transcribing...")
                user_text = transcribe_audio()
                print(f"You said: {user_text}")

                if not user_text: continue

                if "goodbye" in user_text.lower() or "good bye" in user_text.lower() or "bye" in user_text.lower():
                    print("Tutor: Goodbye!")
                    stream.feed("Goodbye! Have a great day.")
                    stream.play()
                    break

                print("Thinking...")
                ai_response = chat_with_ollama(user_text, history)
                
                print(f"Tutor: {ai_response}")
                
                # Speak the response
                stream.feed(ai_response)
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
