# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from model_loader import ConversationalRAG
import time
import threading
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# --- CONFIGURATION for SESSION CLEANUP ---
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
CLEANUP_INTERVAL_SECONDS = 600 # 10 minutes

# A thread-safe dictionary to hold active RAG instances
active_sessions = {}
_sessions_lock = threading.Lock()

# --- NEW: Dedicated Initialization Endpoint ---
@app.route("/api/init", methods=["POST"])
def init_session():
    """Handles the slow creation of a new session."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        session_id = data.get("session_id")
        if not session_id:
            return jsonify({"error": "Missing 'session_id'"}), 400

        with _sessions_lock:
            if session_id not in active_sessions:
                logger.info(f"INITIALIZING new RAG instance for session: {session_id}")
                try:
                    # This is the slow part: loading models, creating vector store, etc.
                    active_sessions[session_id] = ConversationalRAG(session_id=session_id)
                    logger.info(f"Initialization SUCCESS for session: {session_id}")
                except Exception as e:
                    logger.error(f"Initialization FAILED for session {session_id}: {e}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    return jsonify({"error": f"Failed to initialize session: {str(e)}"}), 500
            else:
                logger.info(f"Session already initialized: {session_id}")
        
        # Get welcome message (potentially translated)
        try:
            rag_instance = active_sessions[session_id]
            welcome_message = rag_instance.get_welcome_message()
        except Exception as e:
            logger.error(f"Error getting welcome message: {e}")
            welcome_message = "Hello! How can I help you?"
        
        return jsonify({
            "status": "initialized", 
            "message": "Session is ready.",
            "welcome_message": welcome_message
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in init_session: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# --- Background Cleanup Task (Improved with error handling) ---
def cleanup_inactive_sessions():
    """This function runs in a background thread and cleans up old sessions."""
    while True:
        try:
            logger.info(f"BACKGROUND_TASK: Running session cleanup. {len(active_sessions)} sessions active.")
            inactive_session_ids = []
            current_time = time.time()
            with _sessions_lock:
                for session_id, rag_instance in list(active_sessions.items()):
                    if current_time - rag_instance.last_used > SESSION_TIMEOUT_SECONDS:
                        inactive_session_ids.append(session_id)
                        
            if inactive_session_ids:
                logger.info(f"BACKGROUND_TASK: Found {len(inactive_session_ids)} inactive session(s) to clean up.")
                for session_id in inactive_session_ids:
                    try:
                        with _sessions_lock:
                            if session_id in active_sessions:
                                active_sessions[session_id].complete_system_reset()
                                del active_sessions[session_id]
                                logger.info(f"BACKGROUND_TASK: Cleaned up session {session_id}.")
                    except Exception as e:
                        logger.error(f"Error cleaning up session {session_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")
            
        time.sleep(CLEANUP_INTERVAL_SECONDS)

# --- API Endpoints (Modified to be thread-safe with better error handling) ---
@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        query = data.get("query")
        session_id = data.get("session_id")
        
        if not query:
            return jsonify({"error": "Missing 'query'"}), 400
        if not session_id:
            return jsonify({"error": "Missing 'session_id'"}), 400
            
        query = query.strip()
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        with _sessions_lock:
            # The session should already exist, but this is a fallback.
            if session_id not in active_sessions:
                logger.error(f"Session {session_id} not found in active sessions")
                return jsonify({"error": "Session not initialized. Please refresh."}), 400
            rag_instance = active_sessions[session_id]
        
        try:
            logger.info(f"Processing query for session {session_id}: {query[:50]}...")
            response = rag_instance.query_with_context(query)
            logger.info(f"Successfully processed query for session {session_id}")
            return jsonify({"response": response})
            
        except Exception as e:
            logger.error(f"Error processing query for session {session_id}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return jsonify({"error": f"Error processing query: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in ask endpoint: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    try:
        data = request.get_json()
        session_id = data.get("session_id") if data else None
        
        with _sessions_lock:
            if session_id and session_id in active_sessions:
                try:
                    rag_instance = active_sessions[session_id]
                    rag_instance.complete_system_reset()
                    del active_sessions[session_id]
                    logger.info(f"Successfully reset session: {session_id}")
                except Exception as e:
                    logger.error(f"Error resetting session {session_id}: {e}")
                    return jsonify({"error": f"Error resetting session: {str(e)}"}), 500
                    
        return jsonify({"message": "Session reset successful"})
        
    except Exception as e:
        logger.error(f"Unexpected error in reset endpoint: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy", 
        "active_sessions": len(active_sessions),
        "timestamp": time.time()
    })

# Error handler for 404s
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

# Error handler for 500s
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_inactive_sessions, daemon=True)
    cleanup_thread.start()
    logger.info("Starting Flask server on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=False)