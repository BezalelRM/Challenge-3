#!/bin/bash

echo "🚀 AI Smart Tutor - Starting Application"
echo "========================================"
echo ""

# Check if MySQL is running
echo "🔍 Checking MySQL..."
if ! pgrep -x "mysqld" > /dev/null; then
    echo "⚠️  MySQL is not running!"
    echo "   Start it with: brew services start mysql"
    echo ""
    read -p "Do you want to start MySQL now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        brew services start mysql
        sleep 3
    else
        echo "❌ Cannot start without MySQL. Exiting..."
        exit 1
    fi
fi

echo "✅ MySQL is running"
echo ""

# Check if virtual environment exists
if [ ! -d "server/venv" ]; then
    echo "📦 Virtual environment not found. Setting up..."
    cd server
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Setup complete!"
    echo ""
fi

# Start backend in background
echo "🔧 Starting Backend Server..."
cd server
source venv/bin/activate
python app.py &
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

echo "========================================"
echo "🎉 Application is ready!"
echo ""
echo "📱 Open in browser:"
echo "   http://localhost:8000/login.html"
echo ""
echo "🛑 To stop the servers:"
echo "   Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo "========================================"
echo ""

# Keep script running
wait
