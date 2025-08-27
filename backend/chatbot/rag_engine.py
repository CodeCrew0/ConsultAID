import os
import requests
import json
import re
import chromadb
from sentence_transformers import SentenceTransformer
from langdetect import detect, LangDetectError
from typing import List, Dict, Tuple
from django.conf import settings
from .document_processor import DocumentProcessor

class RAGEngine:
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(settings.VECTOR_DB_PATH))
        self.collection = self.chroma_client.get_or_create_collection(
            name="campus_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model
        print("Loading multilingual embedding model...")
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Initialize document processor
        self.doc_processor = DocumentProcessor()
        
        # Ollama settings
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_MODEL
        
        # Language detection
        self.language_map = {
            'en': 'English',
            'hi': 'Hindi',
            'hinglish': 'Hinglish'
        }
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            detected = detect(text)
            # Simple heuristic for Hinglish detection
            if detected == 'en':
                # Check if contains Hindi/Devanagari characters or common Hinglish patterns
                hindi_chars = bool(re.search(r'[\u0900-\u097F]', text))
                hinglish_patterns = bool(re.search(r'\b(hai|hain|kar|kya|kaise|kyun|main|mein|ye|wo|iska|uska)\b', text.lower()))
                
                if hindi_chars or hinglish_patterns:
                    return 'hinglish'
            
            return detected if detected in ['en', 'hi'] else 'en'
        except LangDetectError:
            return 'en'  # Default to English
    
    def add_documents(self, documents_dir: str) -> int:
        """Process and add documents to vector database"""
        added_count = 0
        
        for root, dirs, files in os.walk(documents_dir):
            for file in files:
                if file.lower().endswith(('.pdf', '.txt', '.docx')):
                    file_path = os.path.join(root, file)
                    
                    # Check if already processed
                    file_hash = self.doc_processor.get_file_hash(file_path)
                    existing = self.collection.get(where={"file_hash": file_hash})
                    
                    if not existing['ids']:
                        chunks = self.doc_processor.process_document(file_path)
                        
                        if chunks:
                            self._add_chunks_to_db(chunks)
                            added_count += 1
                            print(f"Added: {file}")
        
        print(f"Total documents added: {added_count}")
        return added_count
    
    def _add_chunks_to_db(self, chunks: List[Dict]):
        """Add text chunks to ChromaDB"""
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.encode(texts).tolist()
        
        ids = [f"{chunk['metadata']['file_hash']}_{i}" for i, chunk in enumerate(chunks)]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def retrieve_context(self, query: str, top_k: int = 4) -> List[Dict]:
        """Retrieve relevant context for query"""
        query_embedding = self.embedder.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        contexts = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                context = {
                    'text': doc,
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                contexts.append(context)
        
        return contexts
    
    def call_ollama(self, prompt: str) -> str:
        """Call Ollama API for text generation"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_ctx": 2048
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return "Sorry, I'm having trouble connecting to the language model."
                
        except Exception as e:
            print(f"Ollama API error: {e}")
            return "Sorry, I encountered an error while processing your request."
    
    def generate_response(self, query: str, language: str = 'en') -> Tuple[str, float]:
        """Generate response using RAG pipeline"""
        # Retrieve relevant contexts
        contexts = self.retrieve_context(query)
        
        if not contexts:
            return self._get_fallback_response(language), 0.0
        
        # Prepare context for prompt
        context_text = "\n\n".join([ctx['text'] for ctx in contexts])
        confidence = sum([ctx['score'] for ctx in contexts]) / len(contexts)
        
        # Create language-aware prompt
        prompt = self._create_prompt(query, context_text, language)
        
        # Generate response
        response = self.call_ollama(prompt)
        
        return response, confidence
    
    def _create_prompt(self, query: str, context: str, language: str) -> str:
        """Create language-aware prompt for Ollama"""
        if language == 'hi':
            system_msg = """आप एक सहायक कैंपस चैटबॉट हैं। दिए गए संदर्भ के आधार पर हिंदी में उत्तर दें। यदि जानकारी उपलब्ध नहीं है, तो विनम्रता से कहें कि आप नहीं जानते।"""
        elif language == 'hinglish':
            system_msg = """You are a helpful campus chatbot. Answer in Hinglish (Hindi-English mix) based on the given context. If information is not available, politely say you don't know."""
        else:
            system_msg = """You are a helpful campus chatbot. Answer in English based on the given context. If the information is not available, politely say you don't know."""
        
        prompt = f"""
{system_msg}

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def _get_fallback_response(self, language: str) -> str:
        """Return fallback response when no context found"""
        fallbacks = {
            'en': "I don't have specific information about that. Please contact the administration office for more details.",
            'hi': "मुझे इसके बारे में विशिष्ट जानकारी नहीं है। कृपया अधिक विवरण के लिए प्रशासन कार्यालय से संपर्क करें।",
            'hinglish': "Mujhe iske baare mein specific information nahi hai. Please administration office se contact kijiye."
        }
        return fallbacks.get(language, fallbacks['en'])

# Initialize global RAG engine
rag_engine = None

def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine