# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from model_loader import ConversationalRAG
import time
import threading

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
    data = request.get_json()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing 'session_id'"}), 400

    with _sessions_lock:
        if session_id not in active_sessions:
            print(f"INITIALIZING new RAG instance for session: {session_id}")
            try:
                # This is the slow part: loading models, creating vector store, etc.
                active_sessions[session_id] = ConversationalRAG(session_id=session_id)
                print(f"Initialization SUCCESS for session: {session_id}")
            except Exception as e:
                print(f"Initialization FAILED for session {session_id}: {e}")
                return jsonify({"error": "Failed to initialize session"}), 500
        else:
            print(f"Session already initialized: {session_id}")
    
    return jsonify({"status": "initialized", "message": "Session is ready."}), 200


# --- Background Cleanup Task (Unchanged) ---
def cleanup_inactive_sessions():
    """This function runs in a background thread and cleans up old sessions."""
    while True:
        print(f"BACKGROUND_TASK: Running session cleanup. {len(active_sessions)} sessions active.")
        inactive_session_ids = []
        current_time = time.time()
        with _sessions_lock:
            for session_id, rag_instance in list(active_sessions.items()):
                if current_time - rag_instance.last_used > SESSION_TIMEOUT_SECONDS:
                    inactive_session_ids.append(session_id)
        if inactive_session_ids:
            print(f"BACKGROUND_TASK: Found {len(inactive_session_ids)} inactive session(s) to clean up.")
            for session_id in inactive_session_ids:
                with _sessions_lock:
                    if session_id in active_sessions:
                        active_sessions[session_id].complete_system_reset()
                        del active_sessions[session_id]
                        print(f"BACKGROUND_TASK: Cleaned up session {session_id}.")
        time.sleep(CLEANUP_INTERVAL_SECONDS)

# --- API Endpoints (Modified to be thread-safe) ---
@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query")
    session_id = data.get("session_id")
    
    if not all([query, session_id]):
        return jsonify({"error": "Missing 'query' or 'session_id'"}), 400

    with _sessions_lock:
        # The session should already exist, but this is a fallback.
        if session_id not in active_sessions:
            return jsonify({"error": "Session not initialized. Please refresh."}), 400
        rag_instance = active_sessions[session_id]
    
    try:
        response = rag_instance.query_with_context(query)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json()
    session_id = data.get("session_id")
    with _sessions_lock:
        if session_id and session_id in active_sessions:
            rag_instance = active_sessions[session_id]
            rag_instance.complete_system_reset()
            del active_sessions[session_id]
    return jsonify({"message": "Session reset successful"})

if __name__ == "__main__":
    cleanup_thread = threading.Thread(target=cleanup_inactive_sessions, daemon=True)
    cleanup_thread.start()
    app.run(host="0.0.0.0", port=5001, debug=False)