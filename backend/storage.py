import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import os

class Storage:
    """Lightweight in-memory storage with JSON persistence"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # In-memory storage
        self.users: Dict[str, dict] = {}
        self.questions: List[dict] = []
        self.textbook_chunks: List[dict] = []
        self.quizzes: Dict[str, dict] = {}
        
        # Load persisted data
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON files"""
        try:
            if os.path.exists(f"{self.data_dir}/users.json"):
                with open(f"{self.data_dir}/users.json", "r") as f:
                    self.users = json.load(f)
            
            if os.path.exists(f"{self.data_dir}/questions.json"):
                with open(f"{self.data_dir}/questions.json", "r") as f:
                    self.questions = json.load(f)
            
            if os.path.exists(f"{self.data_dir}/textbook_chunks.json"):
                with open(f"{self.data_dir}/textbook_chunks.json", "r") as f:
                    self.textbook_chunks = json.load(f)
            
            if os.path.exists(f"{self.data_dir}/quizzes.json"):
                with open(f"{self.data_dir}/quizzes.json", "r") as f:
                    self.quizzes = json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def _save_users(self):
        """Persist users to JSON"""
        with open(f"{self.data_dir}/users.json", "w") as f:
            json.dump(self.users, f, indent=2)
    
    def _save_questions(self):
        """Persist questions to JSON"""
        with open(f"{self.data_dir}/questions.json", "w") as f:
            json.dump(self.questions, f, indent=2)
    
    def _save_textbook_chunks(self):
        """Persist textbook chunks to JSON"""
        with open(f"{self.data_dir}/textbook_chunks.json", "w") as f:
            json.dump(self.textbook_chunks, f, indent=2)
    
    def _save_quizzes(self):
        """Persist quizzes to JSON"""
        with open(f"{self.data_dir}/quizzes.json", "w") as f:
            json.dump(self.quizzes, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_user_id(self, username: str) -> str:
        """Generate unique user ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{username}{timestamp}".encode()).hexdigest()[:12]
    
    # User operations
    def create_user(self, username: str, password: str, grade: str = "10") -> str:
        """Create a new user"""
        # Check if username exists
        for user_id, user in self.users.items():
            if user["username"] == username:
                raise ValueError("Username already exists")
        
        user_id = self._generate_user_id(username)
        self.users[user_id] = {
            "user_id": user_id,
            "username": username,
            "password": self._hash_password(password),
            "grade": grade,
            "score": 0,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_users()
        return user_id
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user and return user data"""
        hashed_password = self._hash_password(password)
        
        for user_id, user in self.users.items():
            if user["username"] == username and user["password"] == hashed_password:
                return user
        
        return None
    
    def get_user(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def update_user_score(self, user_id: str, points: int):
        """Update user score"""
        if user_id in self.users:
            self.users[user_id]["score"] += points
            self._save_users()
    
    # Question operations
    def add_question(self, question_data: dict):
        """Add question to history"""
        self.questions.append(question_data)
        self._save_questions()
    
    def get_user_questions(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get user's question history"""
        user_questions = [q for q in self.questions if q["user_id"] == user_id]
        return sorted(user_questions, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    
    # Textbook operations
    def add_textbook_chunks(self, chunks: List[dict], replace_existing: bool = True):
        """Add textbook chunks, optionally replacing existing content"""
        if replace_existing:
            # Clear existing chunks and add new ones
            self.textbook_chunks = chunks
            print(f"Replaced textbook content with {len(chunks)} new chunks")
        else:
            # Append to existing chunks
            self.textbook_chunks.extend(chunks)
            print(f"Added {len(chunks)} chunks to existing textbook content")
        
        self._save_textbook_chunks()
    
    def clear_textbook_chunks(self):
        """Clear all textbook chunks"""
        self.textbook_chunks = []
        self._save_textbook_chunks()
        print("Cleared all textbook content")
    
    def get_textbook_chunks(self, grade: Optional[str] = None) -> List[dict]:
        """Get textbook chunks, optionally filtered by grade"""
        if grade:
            return [c for c in self.textbook_chunks if c.get("grade") == grade]
        return self.textbook_chunks
    
    # Leaderboard
    def get_leaderboard(self, limit: int = 50) -> List[dict]:
        """Get top users by score"""
        sorted_users = sorted(
            self.users.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:limit]
        
        return [
            {
                "username": u["username"],
                "grade": u["grade"],
                "score": u["score"]
            }
            for u in sorted_users
        ]
    
    # System stats
    def get_system_stats(self) -> dict:
        """Get system-wide statistics"""
        total_users = len(self.users)
        total_questions = len(self.questions)
        total_chunks = len(self.textbook_chunks)
        total_quizzes = len(self.quizzes)
        
        total_tokens_saved = sum(q.get("tokens_saved", 0) for q in self.questions)
        avg_compression = sum(q.get("compression_rate", 0) for q in self.questions) / total_questions if total_questions > 0 else 0
        
        return {
            "total_users": total_users,
            "total_questions": total_questions,
            "total_textbook_chunks": total_chunks,
            "total_quizzes": total_quizzes,
            "total_tokens_saved": total_tokens_saved,
            "avg_compression_rate": round(avg_compression, 2)
        }
    
    # Quiz operations
    def store_quiz(self, user_id: str, questions: List[dict]) -> str:
        """Store a generated quiz"""
        quiz_id = hashlib.md5(f"{user_id}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        self.quizzes[quiz_id] = {
            "quiz_id": quiz_id,
            "user_id": user_id,
            "questions": questions,
            "answers": {},
            "score": None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        self._save_quizzes()
        return quiz_id
    
    def get_quiz(self, quiz_id: str) -> Optional[dict]:
        """Get quiz by ID"""
        return self.quizzes.get(quiz_id)
    
    def update_quiz_results(self, quiz_id: str, answers: dict, score_result: dict):
        """Update quiz with answers and score"""
        if quiz_id in self.quizzes:
            self.quizzes[quiz_id]["answers"] = answers
            self.quizzes[quiz_id]["score"] = score_result
            self.quizzes[quiz_id]["completed_at"] = datetime.now().isoformat()
            self._save_quizzes()
    
    def get_user_quizzes(self, user_id: str) -> List[dict]:
        """Get user's quiz history"""
        user_quizzes = [q for q in self.quizzes.values() if q["user_id"] == user_id]
        return sorted(user_quizzes, key=lambda x: x.get("created_at", ""), reverse=True)
