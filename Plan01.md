# Digital English Tutor: Offline Architecture Plan

## The Architecture: "Ear, Brain, and Mouth"

Since the goal is to run this entirely offline on a Windows machine, we will treat the local computer as a server. We need three distinct components working in a Python loop:

1.  **The Ear (Speech-to-Text / STT):** Captures voice and converts it to text.
2.  **The Brain (The LLM):** Receives the text, "thinks" as an English tutor, and generates a text response.
3.  **The Mouth (Text-to-Speech / TTS):** Reads the AI's response back to the user.

### Privacy & Cost Note
In this architecture, we are performing **Inference**, not Training.

*   **Cost:** **$0**. All software (Ollama, Python, Libraries) and Models (Llama 3, Whisper) used here are Open Source or Open Weights and free to use locally. No API keys or credit cards are required.
*   **Inference:** Using the model to get an answer. This does not save data or learn from the voice.
*   **Training:** Updating the model's weights. We will *not* build a training loop. Voice data stays in RAM and is flushed when the script closes.

---

## Three Approaches (From Easiest to "Pro")

Given the constraints (Windows, Python, Learning Goal), here are the three recommended paths.

### Option 1: The "Ollama" Stack (Recommended Start)
This is the modern standard for running local LLMs easily. It abstracts away complex GPU management so the focus remains on Python logic.

*   **The Brain:** Ollama. It is a tool that lets you run models like Llama 3 or Mistral locally via a simple API.
*   **The Ear:** `Faster-Whisper`. An optimized version of OpenAI's open-source Whisper model. It runs locally and is very accurate with English.
*   **The Mouth:** `RealtimeTTS` (using Coqui/XTTS or System Engine). **Crucial:** `Pyttsx3` is too robotic for language learning; you need proper intonation.

**Why this works:** You don't need to manage CUDA drivers or complex PyTorch installations manually. You just install Ollama, pull a model, and talk to it via Python.

### Option 2: The "All-Python" Hugging Face Stack
This involves loading the models directly in the Python script using the `transformers` library.

*   **The Brain:** A "Quantized" model (GGUF format) loaded via `llama-cpp-python`.
*   **The Ear:** `Whisper` (original OpenAI library).
*   **The Mouth:** `Coqui TTS` (XTTS v2). This is the best open-source voice cloning/synthesis engine, but it is "heavy" to run.

**Why this works:** It gives granular control. However, getting `llama-cpp-python` to compile with GPU acceleration on Windows can be tricky for beginners.

### Option 3: The "Agentic" Learner Stack (The Goal)
This uses the stack from Option 1 but adds a layer of **Agent Logic**. Instead of just "chatting," you build a System Prompt that instructs the AI to behave like two people:

1.  **The Critic:** Checks grammar/syntax.
2.  **The Conversationalist:** Replies to keep the chat going.

You would use a library like LangChain or just pure Python functions to manage this "memory" and flow.

---

## My Recommendation: The "Ollama" Path

I recommend **Option 1 evolving into Option 3**. It is the most frustration-free way to start on Windows, allows you to use your Python skills immediately, and strictly guarantees offline privacy.

---

## The Project Plan

### Phase 1: Setup The "Brain" (Ollama)
1.  Download Ollama for Windows (it installs a small tray icon). [Link to download](https://ollama.com/download/windows)
2.  Open your terminal (Bash) and type: `ollama run llama3` (or `phi3` for lower-end PCs).
3.  This downloads the model (approx 4GB) to your drive. Once it runs, you can chat with it in the terminal. 
4.  **Test:** Disconnect your internet and try it again. It will still work. 
    *   *Success:* You now have an offline AI brain.

### Phase 2: The Python Environment
Since you use VS Code:

1.  **Open your terminal** (ensure you are in the `PersonalEnglishTutor` folder, or create a foleder with desired name).
2.  Create a virtual environment (crucial for keeping dependencies clean):

```bash
python -m venv venv
source venv/Scripts/activate
```
