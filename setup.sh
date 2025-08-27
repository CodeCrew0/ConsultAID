#!/bin/bash

echo "🎓 Campus Chatbot MVP Setup"
echo "=========================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Create project directory
echo "📁 Creating project structure..."
mkdir -p campus_chatbot/{backend,frontend,documents}
cd campus_chatbot

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
cd backend
pip install -r requirements.txt

# Setup Django
echo "🔧 Setting up Django..."
python manage.py migrate
python manage.py collectstatic --noinput

# Pull Ollama model
echo "🤖 Pulling Ollama model (this may take a while)..."
ollama pull mistral:7b

# Start Ollama service
echo "🚀 Starting Ollama service..."
ollama serve &

# Create sample documents directory
echo "📄 Creating sample documents..."
mkdir -p ../documents
echo "Welcome to our campus! This is a sample FAQ document." > ../documents/sample_faq.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "1. Start Ollama: ollama serve"
echo "2. Start Django: cd backend && python manage.py runserver"
echo "3. Open frontend/index.html in your browser"
echo ""
echo "🔧 Admin tasks:"
echo "- Initialize knowledge base: POST to /api/initialize-kb/"
echo "- Upload documents via the admin panel"
echo ""
echo "📚 Example queries to test:"
echo "- 'What are the admission requirements?' (English)"
echo "- 'Campus mein kya facilities hain?' (Hinglish)"
echo "- 'फीस कितनी है?' (Hindi)"