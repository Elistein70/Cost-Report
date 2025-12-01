#!/bin/bash
# ClearDOH Setup Script

echo "🚀 ClearDOH Setup Script"
echo "========================"
echo ""

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install from https://python.org"
    exit 1
fi
echo "✅ Python $(python3 --version) found"

# Check Node
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install from https://nodejs.org"
    exit 1
fi
echo "✅ Node.js $(node --version) found"

# Setup Backend
echo ""
echo "Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env if doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Create directories
mkdir -p uploads output templates data

echo "✅ Backend setup complete!"

cd ..

# Setup Frontend
echo ""
echo "Setting up frontend..."
cd frontend

# Install dependencies
echo "Installing Node dependencies (this may take a few minutes)..."
npm install --silent

echo "✅ Frontend setup complete!"

cd ..

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "To run ClearDOH:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
