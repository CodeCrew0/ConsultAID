# model_loader.py

from langchain_community.llms import ollama
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from datetime import datetime
from translation_service import TranslationService
import os
import json
import shutil
import logging
import time
import traceback

class ConversationalRAG:
    def __init__(self, session_id: str, documents_folder="documents"):
        self.session_id = session_id
        self.session_path = os.path.join("user_sessions", session_id)
        
        # Create session directory with error handling
        try:
            os.makedirs(self.session_path, exist_ok=True)
        except Exception as e:
            raise Exception(f"Could not create session directory: {e}")
            
        self.documents_folder = documents_folder
        self.vector_store_path = os.path.join(self.session_path, "faiss_index")
        self.conversation_file = os.path.join(self.session_path, "conversations.json")
        self.max_context_turns = 5
        
        self.last_used = time.time()  # Record the creation/last used time
        
        # Initialize translation service
        self.translation_service = TranslationService()
        self.user_language = 'en'  # Default to English, will be detected from first message

        self.setup_logging()
        
        try:
            # Check if documents folder exists
            if not os.path.exists(self.documents_folder):
                self.logger.warning(f"Documents folder '{self.documents_folder}' does not exist")
                # Create empty documents folder
                os.makedirs(self.documents_folder, exist_ok=True)
                
            self.conversation_history = self.load_conversation_history()
            self.setup_llm()
            self.setup_embeddings()
            self.setup_vector_store()
            self.setup_qa_chain()
            self.logger.info(f"RAG system initialized for session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def complete_system_reset(self):
        """Clean up session resources"""
        self.logger.info(f"Cleaning up session at: {self.session_path}")
        try:
            # Clean up any model resources first
            if hasattr(self, 'vectorstore'):
                del self.vectorstore
            if hasattr(self, 'qa'):
                del self.qa
            if hasattr(self, 'retriever'):
                del self.retriever
            if hasattr(self, 'llm'):
                del self.llm
            if hasattr(self, 'embeddings'):
                del self.embeddings
            if hasattr(self, 'translation_service'):
                self.translation_service.clear_cache()
                del self.translation_service
                
            # Remove session directory
            if os.path.exists(self.session_path):
                shutil.rmtree(self.session_path)
                self.logger.info(f"Successfully cleaned up session: {self.session_id}")
        except Exception as e:
            self.logger.error(f"Error deleting session directory: {e}")

    def get_welcome_message(self):
        """Get welcome message in user's language"""
        welcome_msg = """Hello! How can I help you?
You can try asking one of these suggestions:
- What is the main topic?
- Can you summarize the key points?"""
        
        if self.user_language != 'en':
            try:
                return self.translation_service.translate_from_english(welcome_msg, self.user_language)
            except:
                return welcome_msg  # Fallback to English
        return welcome_msg

    def setup_logging(self):
        """Set up logging for this instance"""
        self.logger = logging.getLogger(f"{__name__}.{self.session_id}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def setup_llm(self):
        """Initialize the LLM with error handling"""
        try:
            # Check if system prompt file exists
            system_prompt_file = "SYSTEM_MODELFILE.txt"
            if os.path.exists(system_prompt_file):
                with open(system_prompt_file, "r", encoding='utf-8') as f:
                    system_prompt = f.read().strip()
            else:
                self.logger.warning(f"System prompt file '{system_prompt_file}' not found, using default")
                system_prompt = "You are a helpful assistant that answers questions based on the provided context."
                
            self.llm = ollama.Ollama(model="qwen2.5:3b", system=system_prompt)
            self.logger.info("LLM initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting up LLM: {e}")
            raise Exception(f"Failed to initialize LLM: {e}")

    def setup_embeddings(self):
        """Initialize embeddings with error handling"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2",
                model_kwargs={'device': 'cpu'}  # Ensure CPU usage
            )
            self.logger.info("Embeddings initialized successfully")
        except Exception as e:
            self.logger.error(f"Error setting up embeddings: {e}")
            raise Exception(f"Failed to initialize embeddings: {e}")

    def setup_vector_store(self):
        """Initialize vector store with better error handling"""
        try:
            if not os.path.exists(self.vector_store_path):
                self.logger.info("Creating new vector store from documents")
                self.vectorstore = self.create_vector_store_from_documents()
            else:
                self.logger.info("Loading existing vector store")
                self.vectorstore = FAISS.load_local(
                    self.vector_store_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
            self.logger.info("Vector store initialized successfully")
        except Exception as e:
            self.logger.error(f"Error setting up vector store: {e}")
            raise Exception(f"Failed to initialize vector store: {e}")

    def create_vector_store_from_documents(self):
        """Create vector store from PDF documents with comprehensive error handling"""
        try:
            pdf_files = []
            if os.path.exists(self.documents_folder):
                pdf_files = [
                    os.path.join(self.documents_folder, f) 
                    for f in os.listdir(self.documents_folder) 
                    if f.lower().endswith('.pdf')
                ]
            
            if not pdf_files:
                self.logger.warning("No PDF files found, creating empty vector store")
                # Create a dummy document to avoid empty vector store issues
                dummy_doc = Document(
                    page_content="This is a placeholder document. Please upload PDF files to the documents folder.",
                    metadata={"source": "system", "page": 0}
                )
                vectorstore = FAISS.from_documents([dummy_doc], self.embeddings)
                vectorstore.save_local(self.vector_store_path)
                return vectorstore
            
            self.logger.info(f"Processing {len(pdf_files)} PDF files")
            all_docs = []
            
            for pdf_file in pdf_files:
                try:
                    self.logger.info(f"Loading PDF: {pdf_file}")
                    loader = PyPDFLoader(pdf_file)
                    documents = loader.load()
                    
                    if not documents:
                        self.logger.warning(f"No content found in {pdf_file}")
                        continue
                        
                    text_splitter = CharacterTextSplitter(
                        chunk_size=1000, 
                        chunk_overlap=30, 
                        separator="\n"
                    )
                    docs = text_splitter.split_documents(documents)
                    all_docs.extend(docs)
                    self.logger.info(f"Added {len(docs)} chunks from {pdf_file}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing PDF {pdf_file}: {e}")
                    continue
            
            if not all_docs:
                raise Exception("No valid documents could be processed from PDF files")
                
            self.logger.info(f"Creating vector store with {len(all_docs)} total chunks")
            vectorstore = FAISS.from_documents(all_docs, self.embeddings)
            vectorstore.save_local(self.vector_store_path)
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"Error creating vector store: {e}")
            raise Exception(f"Failed to create vector store: {e}")

    def setup_qa_chain(self):
        """Initialize QA chain with error handling"""
        try:
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 3}  # Retrieve top 3 relevant chunks
            )
            self.qa = RetrievalQA.from_chain_type(
                self.llm, 
                chain_type="stuff", 
                retriever=self.retriever,
                return_source_documents=False  # Simplify response
            )
            self.logger.info("QA chain initialized successfully")
        except Exception as e:
            self.logger.error(f"Error setting up QA chain: {e}")
            raise Exception(f"Failed to initialize QA chain: {e}")

    def load_conversation_history(self):
        """Load conversation history with error handling"""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    self.logger.info(f"Loaded {len(history)} conversation turns")
                    return history
        except Exception as e:
            self.logger.error(f"Error loading conversation history: {e}")
        
        return []

    def save_conversation_history(self):
        """Save conversation history with error handling"""
        try:
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving conversation history: {e}")

    def query_with_context(self, query):
        """Process query with conversation context, translation, and comprehensive error handling"""
        try:
            self.last_used = time.time()  # Update the timestamp on every interaction
            
            if not query or not query.strip():
                return "Please provide a valid question."
            
            original_query = query.strip()
            self.logger.info(f"Processing query: {original_query[:100]}...")
            
            # Detect language of the incoming query
            detected_language = self.translation_service.detect_language(original_query)
            self.logger.info(f"Detected language: {detected_language}")
            
            # Set user language if this is the first interaction or if language changed
            if self.user_language == 'en' and detected_language != 'en':
                self.user_language = detected_language
                self.logger.info(f"User language set to: {self.user_language}")
            
            # Translate query to English for processing
            english_query = original_query
            if detected_language != 'en':
                english_query = self.translation_service.translate_to_english(
                    original_query, detected_language
                )
                self.logger.info(f"Translated query to English: {english_query}")
            
            # Build context from recent conversations (using English versions for consistency)
            recent_conversations = self.conversation_history[-self.max_context_turns:]
            context_parts = [
                f"Previous Q: {conv.get('english_query', conv['query'])}\nPrevious A: {conv.get('english_response', conv['response'])}" 
                for conv in recent_conversations
            ]
            context = "\n".join(context_parts)
            
            # Enhanced query with context (in English)
            if context:
                enhanced_query = f"Recent conversation context:\n{context}\n\nCurrent question: {english_query}"
            else:
                enhanced_query = english_query
            
            # Get response from QA chain (in English)
            try:
                response_data = self.qa.invoke({"query": enhanced_query})
                
                # Handle different response formats
                if isinstance(response_data, dict):
                    english_response = response_data.get('result', str(response_data))
                else:
                    english_response = str(response_data)
                    
            except Exception as e:
                self.logger.error(f"Error from QA chain: {e}")
                english_response = "I apologize, but I encountered an error while processing your question. Please try again or rephrase your question."
            
            # Translate response back to user's language
            final_response = english_response
            if self.user_language != 'en':
                final_response = self.translation_service.translate_from_english(
                    english_response, self.user_language
                )
                self.logger.info(f"Translated response to {self.user_language}")
            
            # Save to conversation history (with both versions)
            try:
                conversation_entry = {
                    "query": original_query,
                    "response": final_response,
                    "english_query": english_query,
                    "english_response": english_response,
                    "detected_language": detected_language,
                    "user_language": self.user_language,
                    "timestamp": datetime.now().isoformat()
                }
                self.conversation_history.append(conversation_entry)
                self.save_conversation_history()
            except Exception as e:
                self.logger.error(f"Error saving conversation: {e}")
            
            self.logger.info("Query processed successfully with translation")
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error in query_with_context: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Try to return error message in user's language
            error_message = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            if hasattr(self, 'user_language') and self.user_language != 'en':
                try:
                    error_message = self.translation_service.translate_from_english(
                        error_message, self.user_language
                    )
                except:
                    pass  # If translation fails, return English error
            
            return error_message