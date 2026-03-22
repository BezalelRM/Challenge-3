# 🎓 AI Smart Tutor - Low-Cost Learning Platform

An optimized AI tutoring system for rural students with slow internet. Features token optimization, context pruning, and lightweight Python storage (no MySQL required).

## 🚀 Features

- **No MySQL**: Lightweight Python dictionaries + JSON persistence
- **Token Optimization**: 96% cost savings via ScaleDown API + context pruning
- **PDF Textbook Support**: Upload textbooks, automatic chunking
- **Context Pruning**: Only sends relevant sections to AI (not entire textbook)
- **User Isolation**: Each student has separate data and progress
- **Leaderboard**: Competitive learning with rankings
- **Metrics Tracking**: Monitor tokens saved, compression rate, latency
- **Low Bandwidth**: Optimized for rural students with slow internet

## 📁 Project Structure

```
AI_Smart_Tutor/
├── server/
│   ├── app.py              # Flask backend with MySQL
│   └── requirements.txt    # Python dependencies
├── public/
│   ├── login.html          # Premium login/register page
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Main dashboard
│   ├── leaderboard.html    # Leaderboard with rankings
│   ├── ask.html            # AI chat interface
│   ├── quiz.html           # Quiz interface
│   ├── notes.html          # Notes manager
│   ├── progress.html       # Progress tracker
│   ├── css/
│   │   └── style.css       # Styles
│   ├── js/
│   │   └── script.js       # JavaScript
│   └── assets/
│       └── logo.png        # Logo
└── data/
    └── cache.json          # Cache data
```

## 🛠️ Setup Instructions

### 1. Install MySQL

**macOS:**
```bash
brew install mysql
brew services start mysql
```

**Linux:**
```bash
sudo apt-get install mysql-server
sudo systemctl start mysql
```

### 2. Configure MySQL

```bash
mysql -u root -p
```

Then set your password (update in `server/app.py` line 16):
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_password';
```

### 3. Install Python Dependencies

```bash
cd server
pip3 install -r requirements.txt
```

### 4. Start the Backend Server

```bash
python3 app.py
```

The server will:
- Create the database automatically
- Initialize all tables
- Run on http://localhost:5000

### 5. Start the Frontend

Open a new terminal:

```bash
cd public
python3 -m http.server 8000
```

Or use any static server:
```bash
npx serve public
```

### 6. Access the Application

Open your browser and go to:
```
http://localhost:8000/login.html
```

## 🗄️ Database Schema

The application creates these tables automatically:

- **users**: User accounts (id, username, password, email)
- **user_progress**: Individual progress tracking (points, questions, accuracy, streaks)
- **quiz_history**: Quiz attempt records
- **notes**: User-specific notes
- **chat_history**: AI chat conversations

## 🎯 Usage

1. **Register**: Create a new account on the login page
2. **Login**: Sign in with your credentials
3. **Dashboard**: Access all features from the main dashboard
4. **Learn**: Ask questions, take quizzes, create notes
5. **Compete**: Check the leaderboard to see your ranking
6. **Track**: Monitor your progress and streaks

## 🔒 Security Features

- Password hashing with SHA-256
- Session management
- User-specific data isolation
- SQL injection prevention with parameterized queries

## 🎨 Premium UI Features

- Modern gradient design
- Smooth animations
- Responsive layout
- Glass morphism effects
- Interactive elements
- Real-time updates

## 📊 API Endpoints

- `POST /api/register` - Create new user
- `POST /api/login` - Authenticate user
- `GET /api/progress/<user_id>` - Get user progress
- `PUT /api/progress/<user_id>` - Update progress
- `GET /api/leaderboard` - Get rankings
- `POST /api/quiz/submit` - Submit quiz answer
- `GET /api/notes/<user_id>` - Get user notes
- `POST /api/notes` - Create note
- `POST /api/chat` - AI chat

## 🚀 Next Steps

- Integrate OpenAI API for better AI responses
- Add email verification
- Implement password reset
- Add more quiz categories
- Create achievement badges
- Add social features

## 📝 License

MIT License
