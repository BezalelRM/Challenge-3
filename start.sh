#!/bin/bash

echo "🚀 AI Smart Tutor - Starting Application"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Setup complete!"
    echo ""
fi

# Start backend
echo "🔧 Starting Backend Server..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

sleep 2
echo "✅ Backend running on http://localhost:5000"
echo ""

# Start frontend
echo "🌐 Starting Frontend Server..."
cd public
python3 -m http.server 8000 &
FRONTEND_PID=$!
cd ..

sleep 2
echo "✅ Frontend running on http://localhost:8000"
echo ""

echo "========================================="
echo "🎉 Application is ready!"
echo ""
echo "📱 Open in browser:"
echo "   http://localhost:8000/login.html"
echo ""
echo "🛑 To stop servers:"
echo "   Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo "========================================="
echo ""

# Keep script running
wait
