# 🏗️ System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         STUDENT BROWSER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Login   │  │Dashboard │  │Leaderboard│  │  Upload  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Python)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      main.py (Routes)                     │  │
│  │  /register  /login  /ask  /upload  /leaderboard         │  │
│  └───────┬──────────────────────────────────────────────────┘  │
│          │                                                       │
│  ┌───────▼────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   storage.py   │  │ai_service.py │  │context_pruning  │   │
│  │                │  │              │  │                 │   │
│  │ In-Memory Dict │  │ ScaleDown    │  │ Keyword Match   │   │
│  │ + JSON Files   │  │ API Client   │  │ Relevance Score │   │
│  └────────────────┘  └──────────────┘  └─────────────────┘   │
│                                                                  │
│  ┌──────────────────┐                                          │
│  │ pdf_ingestion.py │                                          │
│  │                  │                                          │
│  │ Chapter Detection│                                          │
│  │ Smart Chunking   │                                          │
│  └──────────────────┘                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENT STORAGE                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ users.json   │  │questions.json│  │textbook_chunks.json  │ │
│  │              │  │              │  │                      │ │
│  │ User accounts│  │ Q&A history  │  │ Textbook content     │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCALEDOWN API (External)                      │
│  https://api.scaledown.xyz/compress/raw                         │
│                                                                  │
│  Input: context + prompt                                        │
│  Output: compressed prompt + AI answer                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Student Asks Question

```
1. STUDENT TYPES QUESTION
   ↓
   "What is photosynthesis?"
   
2. FRONTEND SENDS REQUEST
   ↓
   POST /api/ask
   {
     "user_id": "abc123",
     "question": "What is photosynthesis?",
     "model": "gpt-4o-mini"
   }
   
3. BACKEND: FIND RELEVANT CHUNKS
   ↓
   context_pruner.find_relevant_chunks()
   - Extract keywords: ["photosynthesis"]
   - Score all textbook chunks
   - Select top 5 relevant chunks
   
4. BACKEND: PRUNE CONTEXT
   ↓
   context_pruner.prune_context(chunks, max_tokens=2000)
   - Combine selected chunks
   - Truncate to 2000 tokens
   - Result: "Chapter 5: Photosynthesis is the process..."
   
5. BACKEND: CALL SCALEDOWN API
   ↓
   POST https://api.scaledown.xyz/compress/raw
   {
     "context": "Chapter 5: Photosynthesis...",
     "prompt": "What is photosynthesis?",
     "model": "gpt-4o-mini",
     "scaledown": {"rate": "auto"}
   }
   
6. SCALEDOWN: COMPRESS & GET AI ANSWER
   ↓
   - Compress context: 2000 → 1200 tokens (40% savings)
   - Call OpenAI/Gemini
   - Return answer
   
7. BACKEND: SAVE METRICS
   ↓
   storage.add_question({
     "user_id": "abc123",
     "question": "What is photosynthesis?",
     "answer": "Photosynthesis is...",
     "original_tokens": 2020,
     "compressed_tokens": 1220,
     "tokens_saved": 800,
     "compression_rate": 39.6,
     "latency_ms": 1250
   })
   
8. BACKEND: UPDATE USER SCORE
   ↓
   storage.update_user_score("abc123", +1)
   
9. FRONTEND: DISPLAY ANSWER
   ↓
   Show answer + metrics:
   - Original: 2020 tokens
   - Compressed: 1220 tokens
   - Saved: 800 tokens (39.6%)
   - Latency: 1250ms
```

---

## Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              IN-MEMORY (Runtime)                    │    │
│  │                                                     │    │
│  │  users = {                                         │    │
│  │    "abc123": {                                     │    │
│  │      "username": "student1",                       │    │
│  │      "password": "hashed",                         │    │
│  │      "grade": "10",                                │    │
│  │      "score": 25                                   │    │
│  │    }                                               │    │
│  │  }                                                 │    │
│  │                                                     │    │
│  │  questions = [...]                                 │    │
│  │  textbook_chunks = [...]                           │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ Auto-save on changes             │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │           PERSISTENT (JSON Files)                   │    │
│  │                                                     │    │
│  │  data/users.json                                   │    │
│  │  data/questions.json                               │    │
│  │  data/textbook_chunks.json                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Context Pruning Algorithm

```
INPUT: Question + All Textbook Chunks
OUTPUT: Pruned Context (max 2000 tokens)

STEP 1: Extract Keywords
  "What is photosynthesis?" 
  → ["photosynthesis"]

STEP 2: Score Each Chunk
  For each chunk:
    score = count of keyword occurrences
  
  Chunk 1 (Chapter 5): "photosynthesis" appears 8 times → score = 8
  Chunk 2 (Chapter 3): "photosynthesis" appears 2 times → score = 2
  Chunk 3 (Chapter 7): "photosynthesis" appears 0 times → score = 0

STEP 3: Sort by Score
  [Chunk 1 (score=8), Chunk 2 (score=2), Chunk 3 (score=0)]

STEP 4: Select Top Chunks
  Take top 5 chunks

STEP 5: Combine & Truncate
  Combine chunks until 2000 tokens reached
  
RESULT: Optimized context with only relevant information
```

---

## Token Optimization Pipeline

```
ORIGINAL TEXTBOOK: 50,000 tokens
         │
         │ STEP 1: Context Pruning
         │ (Select relevant chunks)
         ▼
PRUNED CONTEXT: 2,000 tokens (96% reduction)
         │
         │ STEP 2: ScaleDown Compression
         │ (AI-powered compression)
         ▼
COMPRESSED PROMPT: 1,200 tokens (40% additional reduction)
         │
         │ STEP 3: Send to AI Model
         ▼
AI ANSWER: 200 tokens output
         │
         │ TOTAL COST
         ▼
Input:  1,200 tokens × $0.15/1M = $0.00018
Output:   200 tokens × $0.60/1M = $0.00012
TOTAL: $0.0003 per query

SAVINGS: 97.6% vs sending full textbook!
```

---

## Scalability

```
┌─────────────────────────────────────────────────────────┐
│                    PERFORMANCE                           │
│                                                          │
│  Students: 1,000                                        │
│  Questions per day: 10 per student                      │
│  Total queries: 10,000/day                              │
│                                                          │
│  Memory Usage:                                          │
│  - Users: ~1MB                                          │
│  - Questions: ~5MB                                      │
│  - Textbook chunks: ~10MB                               │
│  TOTAL: ~16MB                                           │
│                                                          │
│  Response Time:                                         │
│  - Context pruning: ~50ms                               │
│  - ScaleDown API: ~1000ms                               │
│  - Total: ~1050ms                                       │
│                                                          │
│  Cost:                                                  │
│  - Per query: $0.0003                                   │
│  - Per day: $3                                          │
│  - Per month: $90                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Security Model

```
┌─────────────────────────────────────────────────────────┐
│                    AUTHENTICATION                        │
│                                                          │
│  1. User Registration                                   │
│     - Password hashed with SHA-256                      │
│     - User ID generated with MD5                        │
│     - Stored in users.json                              │
│                                                          │
│  2. User Login                                          │
│     - Password hashed and compared                      │
│     - User ID returned to frontend                      │
│     - Stored in localStorage                            │
│                                                          │
│  3. API Requests                                        │
│     - User ID sent with each request                    │
│     - Backend validates user exists                     │
│     - Data isolated per user                            │
│                                                          │
│  4. Data Isolation                                      │
│     - Each user sees only their data                    │
│     - Questions filtered by user_id                     │
│     - Progress tracked separately                       │
└─────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRODUCTION SETUP                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              FRONTEND (Static)                  │    │
│  │  - Served via Python HTTP server                │    │
│  │  - Or nginx/Apache                              │    │
│  │  - Port 8000                                    │    │
│  └────────────────────────────────────────────────┘    │
│                          │                               │
│                          │ HTTP/JSON                     │
│                          ▼                               │
│  ┌────────────────────────────────────────────────┐    │
│  │           BACKEND (FastAPI)                     │    │
│  │  - Uvicorn ASGI server                         │    │
│  │  - Or Gunicorn + Uvicorn workers               │    │
│  │  - Port 5000                                    │    │
│  └────────────────────────────────────────────────┘    │
│                          │                               │
│                          │ File I/O                      │
│                          ▼                               │
│  ┌────────────────────────────────────────────────┐    │
│  │           DATA (JSON Files)                     │    │
│  │  - data/users.json                             │    │
│  │  - data/questions.json                         │    │
│  │  - data/textbook_chunks.json                   │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

**System is optimized for:**
- ✅ Low cost (96% savings)
- ✅ Low latency (~1s response)
- ✅ Low bandwidth (minimal payloads)
- ✅ Low memory (~16MB for 1000 users)
- ✅ High scalability (async operations)
