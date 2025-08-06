#!/bin/bash

# 🚀 Local Development Startup Script

echo "🏠 Starting Inventory Management System Locally"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.9+ from https://python.org/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check if MongoDB is running (optional)
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB is not running locally. You can:"
    echo "   1. Install and start MongoDB locally"
    echo "   2. Or use MongoDB Atlas (cloud) and update MONGO_URL in backend/.env.local"
fi

echo ""
echo "📁 Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.local .env
    echo "✅ Created backend/.env file"
fi

echo ""
echo "📁 Setting up Frontend..."
cd ../frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    if command -v yarn &> /dev/null; then
        yarn install
    else
        npm install
    fi
fi

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.local .env
    echo "✅ Created frontend/.env file"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "To start the application:"
echo ""
echo "1️⃣  Backend (in one terminal):"
echo "   cd backend"
echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo "   uvicorn server:app --reload --host 0.0.0.0 --port 8001"
echo ""
echo "2️⃣  Frontend (in another terminal):"
echo "   cd frontend"
echo "   npm start  # or yarn start"
echo ""
echo "3️⃣  Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "📝 Make sure MongoDB is running or update MONGO_URL in backend/.env"