# model_loader.py

from langchain_community.llms import ollama
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from datetime import datetime
import os
import json
import shutil
import logging
import time # <-- NEW: Import the time module

class ConversationalRAG:
    def __init__(self, session_id: str, documents_folder="documents"):
        self.session_path = os.path.join("user_sessions", session_id)
        os.makedirs(self.session_path, exist_ok=True)
        self.documents_folder = documents_folder
        self.vector_store_path = os.path.join(self.session_path, "faiss_index")
        self.conversation_file = os.path.join(self.session_path, "conversations.json")
        self.max_context_turns = 5
        
        self.last_used = time.time() # <-- NEW: Record the creation/last used time

        self.setup_logging()
        self.conversation_history = self.load_conversation_history()
        self.setup_llm()
        self.setup_embeddings()
        self.setup_vector_store()
        self.setup_qa_chain()
        self.logger.info(f"RAG system initialized for session: {session_id}")

    def complete_system_reset(self):
        self.logger.info(f"Cleaning up session at: {self.session_path}")
        if os.path.exists(self.session_path):
            try:
                shutil.rmtree(self.session_path)
            except Exception as e:
                self.logger.error(f"Error deleting session directory: {e}")

    def setup_logging(self):
        self.logger = logging.getLogger(f"{__name__}.ConversationalRAG")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def setup_llm(self):
        with open("SYSTEM_MODELFILE.txt", "r") as f:
            system_prompt = f.read()
        self.llm = ollama.Ollama(model="qwen2.5:3b", system=system_prompt)

    def setup_embeddings(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    def setup_vector_store(self):
        if not os.path.exists(self.vector_store_path):
            self.vectorstore = self.create_vector_store_from_documents()
        else:
            self.vectorstore = FAISS.load_local(self.vector_store_path, self.embeddings, allow_dangerous_deserialization=True)

    def create_vector_store_from_documents(self):
        pdf_files = [os.path.join(self.documents_folder, f) for f in os.listdir(self.documents_folder) if f.endswith('.pdf')]
        all_docs = []
        for pdf_file in pdf_files:
            loader = PyPDFLoader(pdf_file)
            documents = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
            docs = text_splitter.split_documents(documents=documents)
            all_docs.extend(docs)
        vectorstore = FAISS.from_documents(all_docs, self.embeddings)
        vectorstore.save_local(self.vector_store_path)
        return vectorstore

    def setup_qa_chain(self):
        self.retriever = self.vectorstore.as_retriever()
        self.qa = RetrievalQA.from_chain_type(self.llm, chain_type="stuff", retriever=self.retriever)

    def load_conversation_history(self):
        try:
            with open(self.conversation_file, 'r', encoding='utf-8') as f: return json.load(f)
        except FileNotFoundError: return []

    def save_conversation_history(self):
        with open(self.conversation_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)

    def query_with_context(self, query):
        self.last_used = time.time() # <-- NEW: Update the timestamp on every interaction
        
        recent_conversations = self.conversation_history[-self.max_context_turns:]
        context_parts = [f"Previous Q: {conv['query']}\nPrevious A: {conv['response']}" for conv in recent_conversations]
        context = "\n".join(context_parts)
        enhanced_query = f"Recent conversation context:\n{context}\n\nCurrent question: {query}" if context else query
        response = self.qa.invoke(enhanced_query)
        response_text = response.get('result', str(response))
        self.conversation_history.append({"query": query, "response": response_text, "timestamp": datetime.now().isoformat()})
        self.save_conversation_history()
        return response_text