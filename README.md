# 🎓 Campus Chatbot MVP

A multilingual RAG-based chatbot for campus queries using Ollama for local LLM inference.

## ✨ Features

- **Local LLM**: Uses Ollama with Mistral 7B running locally
- **Multilingual**: Supports English, Hindi, and Hinglish
- **RAG Pipeline**: ChromaDB + sentence-transformers for context retrieval
- **Privacy-First**: All processing happens locally
- **Easy Deployment**: Simple setup with Django backend + HTML frontend

## 🛠️ Tech Stack

- **Backend**: Django 5.x + Django REST Framework
- **LLM**: Ollama (Mistral 7B)
- **Vector DB**: ChromaDB
- **Embeddings**: paraphrase-multilingual-MiniLM-L12-v2
- **Frontend**: HTML/CSS/JavaScript
- **Language Detection**: langdetect

## ⚡ Quick Setup

### Prerequisites
- Python 3.8+
- 8GB+ RAM (recommended for Mistral 7B)
- GPU optional but recommended

### Installation

```bash
# 1. Clone/download the project
git clone <your-repo> campus_chatbot
cd campus_chatbot

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Start services
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Django
cd backend
source ../venv/bin/activate
python manage.py runserver

# 4. Open frontend/index.html in browser
```

### Manual Setup

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull model
ollama pull mistral:7b

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 4. Setup Django
cd backend
python manage.py migrate
python manage.py collectstatic

# 5. Start services
ollama serve &
python manage.py runserver
```

## 📊 API Endpoints

### Chat API
```bash
POST /api/ask/
{
  "query": "What are the admission requirements?",
  "session_id": "optional-session-id"
}

Response:
{
  "response": "The admission requirements are...",
  "language": "en",
  "confidence": 0.85,
  "session_id": "session_123"
}
```

### Document Management
```bash
# Upload document
POST /api/upload-docs/
FormData: {file: <file>, title: "Document Title"}

# Initialize knowledge base
POST /api/initialize-kb/

# Health check
GET /api/health/

# Clear logs
DELETE /api/delete-logs/?session_id=<session_id>
```

## 📁 Adding Documents

1. **Via Web Interface**: Use the admin panel (⚙️ button)
2. **Direct Upload**: Put files in `documents/` directory and call `/api/initialize-kb/`

Supported formats: PDF, TXT, DOCX

## 🌍 Multilingual Support

The bot automatically detects and responds in:
- **English**: Standard academic English
- **Hindi**: Devanagari script support
- **Hinglish**: Code-switching between Hindi and English

Example queries:
```
English: "What facilities are available on campus?"
Hindi: "कैंपस में कौन सी सुविधाएं उपलब्ध हैं?"
Hinglish: "Campus mein kya facilities available hain?"
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
SECRET_KEY=your-django-secret-key
OLLAMA_MODEL=mistral:7b
OLLAMA_BASE_URL=http://localhost:11434
DEBUG=True
```

### Model Configuration
To use a different Ollama model:
```bash
# Pull new model
ollama pull llama2:7b

# Update settings.py
OLLAMA_MODEL = 'llama2:7b'
```

## 📈 Performance Optimization

### For Better Performance:
1. **GPU Acceleration**: Ensure Ollama uses GPU
2. **Model Selection**: Use smaller models (7B) for faster responses
3. **Chunk Size**: Adjust chunk size in `document_processor.py`
4. **Top-K**: Reduce retrieved chunks for faster processing

### Memory Requirements:
- **Mistral 7B**: ~8GB RAM
- **ChromaDB**: ~1GB for 1000 documents
- **Embeddings**: ~500MB for sentence-transformers

## 🐛 Troubleshooting

### Common Issues:

**1. Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

**2. Model Not Found**
```bash
# List available models
ollama list

# Pull required model
ollama pull mistral:7b
```

**3. Empty Responses**
- Check if documents are uploaded and processed
- Verify embeddings are generated
- Check Ollama model is loaded

**4. Language Detection Issues**
- Ensure proper UTF-8 encoding for Hindi text
- Check if `langdetect` is installed correctly

## 📝 Sample Documents

Create these sample files in `documents/` directory:

**admission_faq.txt**:
```
Admission Requirements:
- 12th grade completion with 75% marks
- Entrance exam score
- Valid ID proof
- Application fee payment

Contact: admissions@college.edu
Phone: +91-9876543210
```

**facilities_hindi.txt**:
```
कैंपस सुविधाएं:
- लाइब्रेरी: 24/7 खुली
- कैंटीन: शाकाहारी और मांसाहारी भोजन
- जिम: आधुनिक उपकरण
- वाई-फाई: पूरे कैंपस में मुफ्त
```

## 🚀 Deployment

### Production Deployment:
1. Set `DEBUG=False` in settings
2. Configure proper database (PostgreSQL)
3. Use Gunicorn/uWSGI for Django
4. Setup Nginx for static files
5. Configure SSL certificates

### Docker Deployment:
```dockerfile
FROM python:3.9
RUN curl -fsSL https://ollama.com/install.sh | sh
# ... rest of Dockerfile
```

## 📞 Support

For issues:
1. Check the troubleshooting section
2. Verify Ollama is running: `ollama list`
3. Check Django logs: `python manage.py runserver --verbosity=2`
4. Test API endpoints with curl/Postman

## 🔒 Privacy & Security

- All processing happens locally
- No external API calls for inference
- Chat logs stored locally (can be cleared)
- File uploads stored in local directory
- Session-based conversation tracking

## 🎯 Future Enhancements
```
- [ ] Voice input/output (STT/TTS)
- [ ] WhatsApp integration
- [ ] Advanced admin dashboard
- [ ] Multi-language context switching
- [ ] Document versioning
- [ ] Analytics dashboard
```