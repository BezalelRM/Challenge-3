from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime

from storage import Storage
from ai_service import AIService
from context_pruning import ContextPruner
from pdf_ingestion import PDFIngestion
from quiz_generator import QuizGenerator

app = FastAPI(title="AI Smart Tutor")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
storage = Storage()
ai_service = AIService()
context_pruner = ContextPruner()
pdf_ingestion = PDFIngestion()
quiz_generator = QuizGenerator()

# Pydantic models
class RegisterRequest(BaseModel):
    username: str
    password: str
    grade: Optional[str] = "10"

class LoginRequest(BaseModel):
    username: str
    password: str

class QuestionRequest(BaseModel):
    user_id: str
    question: str
    model: Optional[str] = "gpt-4o-mini"

class UpdateScoreRequest(BaseModel):
    user_id: str
    points: int

class QuizRequest(BaseModel):
    user_id: str
    grade: Optional[str] = "10"
    num_questions: int = 10

class QuizAnswerRequest(BaseModel):
    user_id: str
    quiz_id: str
    answers: dict

# Authentication endpoints
@app.post("/api/register")
async def register(req: RegisterRequest):
    """Register a new user"""
    try:
        user_id = storage.create_user(req.username, req.password, req.grade)
        return {
            "success": True,
            "message": "Registration successful",
            "user_id": user_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
async def login(req: LoginRequest):
    """Login user"""
    user = storage.authenticate_user(req.username, req.password)
    if user:
        return {
            "success": True,
            "user": {
                "id": user["user_id"],
                "username": user["username"],
                "grade": user["grade"],
                "score": user["score"]
            }
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Textbook ingestion
@app.post("/api/upload-textbook")
async def upload_textbook(file: UploadFile = File(...), grade: str = "10"):
    """Upload and process textbook PDF - replaces existing content"""
    try:
        # Read PDF file
        content = await file.read()
        
        # Extract and chunk text
        chunks = pdf_ingestion.process_pdf(content, grade)
        
        # Replace existing textbook content with new content
        storage.add_textbook_chunks(chunks, replace_existing=True)
        
        return {
            "success": True,
            "message": f"Textbook processed successfully. Replaced existing content with {len(chunks)} new chunks.",
            "chunks_created": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/api/clear-textbook")
async def clear_textbook():
    """Clear all textbook content"""
    try:
        storage.clear_textbook_chunks()
        return {
            "success": True,
            "message": "All textbook content cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing textbook: {str(e)}")

# AI Question endpoint
@app.post("/api/ask")
async def ask_question(req: QuestionRequest):
    """Process student question with context pruning and ScaleDown API"""
    try:
        # Get user
        user = storage.get_user(req.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get relevant textbook chunks
        relevant_chunks = context_pruner.find_relevant_chunks(
            req.question,
            storage.get_textbook_chunks(),
            user["grade"]
        )
        
        # Prune context to most relevant sections
        pruned_context = context_pruner.prune_context(relevant_chunks, max_tokens=2000)
        
        # Call ScaleDown API
        start_time = datetime.now()
        result = await ai_service.get_compressed_answer(
            context=pruned_context,
            question=req.question,
            model=req.model
        )
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calculate metrics
        original_tokens = result.get("original_tokens", 0)
        compressed_tokens = result.get("compressed_tokens", 0)
        tokens_saved = original_tokens - compressed_tokens
        compression_rate = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0
        
        # Store question history
        storage.add_question({
            "user_id": req.user_id,
            "question": req.question,
            "answer": result["answer"],
            "tokens_saved": tokens_saved,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_rate": compression_rate,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update user score (1 point per question)
        storage.update_user_score(req.user_id, 1)
        
        return {
            "success": True,
            "answer": result["answer"],
            "metrics": {
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "tokens_saved": tokens_saved,
                "compression_rate": round(compression_rate, 2),
                "latency_ms": round(latency_ms, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Progress and stats
@app.get("/api/progress/{user_id}")
async def get_progress(user_id: str):
    """Get user progress and statistics"""
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    questions = storage.get_user_questions(user_id)
    
    total_questions = len(questions)
    total_tokens_saved = sum(q.get("tokens_saved", 0) for q in questions)
    avg_compression = sum(q.get("compression_rate", 0) for q in questions) / total_questions if total_questions > 0 else 0
    avg_latency = sum(q.get("latency_ms", 0) for q in questions) / total_questions if total_questions > 0 else 0
    
    return {
        "success": True,
        "progress": {
            "username": user["username"],
            "grade": user["grade"],
            "score": user["score"],
            "total_questions": total_questions,
            "total_tokens_saved": total_tokens_saved,
            "avg_compression_rate": round(avg_compression, 2),
            "avg_latency_ms": round(avg_latency, 2)
        }
    }

# Leaderboard
@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get top students by score"""
    leaderboard = storage.get_leaderboard()
    return {
        "success": True,
        "leaderboard": leaderboard
    }

# Question history
@app.get("/api/questions/{user_id}")
async def get_questions(user_id: str, limit: int = 50):
    """Get user's question history"""
    questions = storage.get_user_questions(user_id, limit)
    return {
        "success": True,
        "questions": questions
    }

# System stats
@app.get("/api/stats")
async def get_stats():
    """Get system-wide statistics"""
    stats = storage.get_system_stats()
    return {
        "success": True,
        "stats": stats
    }

# Quiz endpoints
@app.post("/api/generate-quiz")
async def generate_quiz(req: QuizRequest):
    """Generate a quiz from textbook content"""
    try:
        # Get user
        user = storage.get_user(req.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get textbook chunks for user's grade
        chunks = storage.get_textbook_chunks(req.grade or user["grade"])
        if not chunks:
            raise HTTPException(status_code=400, detail="No textbook content available for this grade")
        
        # Generate quiz
        questions = quiz_generator.generate_quiz(chunks, req.num_questions, req.grade or user["grade"])
        
        # Store quiz
        quiz_id = storage.store_quiz(req.user_id, questions)
        
        return {
            "success": True,
            "quiz_id": quiz_id,
            "questions": questions,
            "total_questions": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/submit-quiz")
async def submit_quiz(req: QuizAnswerRequest):
    """Submit quiz answers and calculate score"""
    try:
        # Get quiz
        quiz = storage.get_quiz(req.quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        if quiz["user_id"] != req.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to submit this quiz")
        
        # Calculate score
        score_result = quiz_generator.calculate_score(req.answers, quiz["questions"])
        
        # Update quiz with results
        storage.update_quiz_results(req.quiz_id, req.answers, score_result)
        
        # Update user score (points based on percentage)
        points = max(1, int(score_result["percentage"] / 10))  # 1-10 points based on percentage
        storage.update_user_score(req.user_id, points)
        
        return {
            "success": True,
            "score": score_result,
            "points_earned": points
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz-history/{user_id}")
async def get_quiz_history(user_id: str):
    """Get user's quiz history"""
    try:
        quizzes = storage.get_user_quizzes(user_id)
        return {
            "success": True,
            "quizzes": quizzes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
