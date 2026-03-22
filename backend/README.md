# AI Smart Tutor Backend

Lightweight Python backend with FastAPI, in-memory storage, and ScaleDown API integration.

## Features

- ✅ No MySQL dependency - uses Python dictionaries + JSON persistence
- ✅ FastAPI for high performance
- ✅ ScaleDown API integration for token optimization
- ✅ Context pruning to minimize API costs
- ✅ PDF textbook ingestion and chunking
- ✅ User authentication and progress tracking
- ✅ Leaderboard system
- ✅ Metrics collection (tokens saved, compression rate, latency)

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run server:
```bash
python main.py
```

Server runs on: http://localhost:5000

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user

### Textbook
- `POST /api/upload-textbook` - Upload PDF textbook

### AI Question
- `POST /api/ask` - Ask question with context pruning

### Progress
- `GET /api/progress/{user_id}` - Get user progress
- `GET /api/questions/{user_id}` - Get question history

### Leaderboard
- `GET /api/leaderboard` - Get top students

### System
- `GET /api/stats` - System statistics
- `GET /health` - Health check

## Data Storage

Data is stored in `data/` directory:
- `users.json` - User accounts
- `questions.json` - Question history
- `textbook_chunks.json` - Textbook content

## Architecture

```
backend/
├── main.py              # FastAPI app & routes
├── storage.py           # In-memory storage with JSON persistence
├── ai_service.py        # ScaleDown API integration
├── context_pruning.py   # Context optimization
├── pdf_ingestion.py     # PDF processing
└── requirements.txt     # Dependencies
```

## Optimization Features

1. **Context Pruning**: Only sends relevant textbook sections to AI
2. **ScaleDown API**: Compresses prompts to reduce tokens
3. **In-Memory Storage**: Fast data access without database overhead
4. **Async Operations**: Non-blocking API calls
5. **Metrics Tracking**: Monitor token savings and performance
