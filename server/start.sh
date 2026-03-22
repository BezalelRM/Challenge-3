#!/bin/bash

echo "🚀 Starting AI Smart Tutor Backend..."
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "🗄️  Starting Flask server..."
echo "Server will run on http://localhost:5000"
echo ""
python3 app.py
