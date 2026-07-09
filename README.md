# AI Teacher Assistant

Virtual classroom platform with AI Q&A, WebRTC, live subtitles, and attendance.

## Features
- Real-time video/audio via WebRTC
- AI transcription and subtitles
- Live chat and Q&A

## Setup
1. Create a `.env` file based on `.env.example`.
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Run server: `uvicorn backend.main:app --reload --port 8000`
