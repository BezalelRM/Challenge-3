from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# MySQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update with your MySQL password
    'database': 'ai_tutor'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize database and create tables"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        cursor.execute("CREATE DATABASE IF NOT EXISTS ai_tutor")
        cursor.execute("USE ai_tutor")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                total_questions INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                total_time_spent INT DEFAULT 0,
                streak_days INT DEFAULT 0,
                last_activity DATE,
                points INT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                question TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct BOOLEAN,
                time_taken INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                subject VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Database initialized successfully!")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email", "")
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    
    try:
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
            (username, hashed_password, email)
        )
        user_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO user_progress (user_id) VALUES (%s)", (user_id,))
        
        connection.commit()
        return jsonify({"success": True, "message": "Registration successful"})
    
    except mysql.connector.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists"}), 400
    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        hashed_password = hash_password(password)
        cursor.execute(
            "SELECT id, username FROM users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )
        user = cursor.fetchone()
        
        if user:
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            connection.commit()
            
            return jsonify({
                "success": True,
                "user": {"id": user['id'], "username": user['username']}
            })
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/api/progress/<int:user_id>", methods=["GET"])
def get_progress(user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        progress = cursor.fetchone()
        return jsonify({"success": True, "progress": progress})
    finally:
        cursor.close()
        connection.close()

@app.route("/api/progress/<int:user_id>", methods=["PUT"])
def update_progress(user_id):
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE user_progress 
            SET total_questions = %s, correct_answers = %s, 
                total_time_spent = %s, points = %s, last_activity = CURDATE()
            WHERE user_id = %s
        """, (
            data.get('total_questions', 0),
            data.get('correct_answers', 0),
            data.get('total_time_spent', 0),
            data.get('points', 0),
            user_id
        ))
        connection.commit()
        return jsonify({"success": True})
    finally:
        cursor.close()
        connection.close()

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.username, up.points, up.correct_answers, 
                   up.total_questions, up.streak_days
            FROM users u
            JOIN user_progress up ON u.id = up.user_id
            ORDER BY up.points DESC, up.correct_answers DESC
            LIMIT 50
        """)
        leaderboard = cursor.fetchall()
        return jsonify({"success": True, "leaderboard": leaderboard})
    finally:
        cursor.close()
        connection.close()

@app.route("/api/quiz/submit", methods=["POST"])
def submit_quiz():
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO quiz_history 
            (user_id, question, user_answer, correct_answer, is_correct, time_taken)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.get('user_id'),
            data.get('question'),
            data.get('user_answer'),
            data.get('correct_answer'),
            data.get('is_correct'),
            data.get('time_taken', 0)
        ))
        connection.commit()
        return jsonify({"success": True})
    finally:
        cursor.close()
        connection.close()

@app.route("/api/notes/<int:user_id>", methods=["GET"])
def get_notes(user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM notes WHERE user_id = %s ORDER BY updated_at DESC", (user_id,))
        notes = cursor.fetchall()
        return jsonify({"success": True, "notes": notes})
    finally:
        cursor.close()
        connection.close()

@app.route("/api/notes", methods=["POST"])
def create_note():
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO notes (user_id, title, content, subject)
            VALUES (%s, %s, %s, %s)
        """, (data.get('user_id'), data.get('title'), data.get('content'), data.get('subject', '')))
        connection.commit()
        return jsonify({"success": True, "note_id": cursor.lastrowid})
    finally:
        cursor.close()
        connection.close()

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get('user_id')
    question = data.get('question')
    
    answer = f"AI Response: This is a helpful answer to your question about '{question}'"
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO chat_history (user_id, question, answer)
                VALUES (%s, %s, %s)
            """, (user_id, question, answer))
            connection.commit()
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({"success": True, "answer": answer})

if __name__ == "__main__":
    init_database()
    app.run(debug=True, port=5000)
