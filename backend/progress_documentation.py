"""
Documentation for the Progress Tracking API Endpoint

This module documents the implementation and data structure of the learning progress 
system within the AI Smart Tutor application.

Endpoint: GET /api/progress/{user_id}
Description: Retrieves comprehensive performance metrics and learning statistics for a specific user.

Data Structure Returned:
-----------------------
{
    "success": bool,
    "progress": {
        "username": str,             # User's display name
        "grade": str,                # Current grade level (e.g., "10")
        "score": int,                # Total accumulated points from quizzes/activities
        "total_questions": int,      # Count of questions asked by the user
        "total_tokens_saved": int,   # Efficiency metric: total LLM tokens saved via context pruning
        "avg_compression_rate": float, # Average percentage of context removed by the pruner
        "avg_latency_ms": float      # Average response time from the AI service in milliseconds
    }
}

Functionality:
--------------
1. Validates user existence via the Storage service.
2. Aggregates historical question data belonging to the user.
3. Calculates efficiency metrics (compression and latency) from historical metadata.

Implementation Detail (from main.py):
------------------------------------
@app.get("/api/progress/{user_id}")
async def get_progress(user_id: str):
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
        "progress": { ... }
    }

Usage in Frontend:
------------------
The 'progress.html' file utilizes Chart.js to visualize these metrics, specifically:
- Learning progress over time.
- Efficiency of AI interactions (tokens saved).
- Quiz performance trends.
"""

def get_progress_documentation():
    """Returns a dictionary representing the progress tracking schema."""
    return {
        "endpoint": "/api/progress/{user_id}",
        "method": "GET",
        "fields": [
            "username", 
            "grade", 
            "score", 
            "total_questions", 
            "total_tokens_saved", 
            "avg_compression_rate", 
            "avg_latency_ms"
        ]
    }
