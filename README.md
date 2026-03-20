# AI Transcriber

A simple Windows desktop application that records your voice and transcribes it using OpenAI's Whisper API.

## Features

- **Voice Recording** — Click to start/stop recording your microphone
- **12-Minute Timer** — Elapsed and remaining time display with auto-stop at the limit
- **Whisper Transcription** — Sends audio to OpenAI's Whisper API and returns text
- **Editable Text Box** — Review and edit your transcription
- **Append Mode** — Multiple recordings append to existing text
- **Copy to Clipboard** — One-click copy of all transcribed text
- **Clear & Undo** — Clear the text box with the ability to undo
- **API Key Persistence** — Your OpenAI API key is saved locally between sessions

## Quick Start

### Option 1: Run the `.exe` (no Python required)

1. Download `AI-Transcriber.exe` from the [Releases](https://github.com/bradfordsummers/AI-Transcriber/releases) page
2. Double-click to launch
3. Enter your OpenAI API key and click **Save Key**
4. Start recording!

### Option 2: Run from source

```bash
# Clone the repo
git clone https://github.com/bradfordsummers/AI-Transcriber.git
cd AI-Transcriber

# Create a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## Building the `.exe`

Make sure you've installed the dependencies (including `pyinstaller`), then run:

```bash
build_exe.bat
```

The standalone `.exe` will be created in the `dist/` folder.

## Configuration

Your OpenAI API key is stored in `config.json` next to the executable (or in the project directory when running from source). This file is gitignored and never committed to version control.

## Requirements

- Windows 10/11
- A working microphone
- An [OpenAI API key](https://platform.openai.com/api-keys) with access to the Whisper API

## Tech Stack

- **Python 3.11+**
- **customtkinter** — Modern GUI framework
- **sounddevice** — Audio recording
- **scipy / numpy** — WAV file handling
- **openai** — Whisper API client
- **PyInstaller** — Standalone `.exe` packaging

## License

MIT
