# Telegram Voice AI + Image Bot

Telegram bot that:
- generates images from text prompts (OpenAI Images)
- listens to voice messages, converts to text (speech recognition)
- replies with AI answer (OpenAI Chat)
- optionally replies with voice (gTTS + pydub)

## Features
- Text → image generation
- Voice → speech-to-text → AI answer
- Voice reply (TTS)
- Logging to file + console

## Tech Stack
Python • python-telegram-bot • OpenAI • SpeechRecognition • gTTS • pydub

## Setup
### 1) Create virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

#Install dependencies
pip install -r requirements.txt

#Install FFmpeg (required for pydub)

Windows: install FFmpeg and add it to PATH

Linux: sudo apt-get install ffmpeg

Mac: brew install ffmpeg

#Create .env

Copy .env.example to .env and fill:

TELEGRAM_TOKEN

OPENAI_API_KEY

# Windows:
copy .env.example .env
# Linux/Mac:
cp .env.example .env

#Run
python bot.py
