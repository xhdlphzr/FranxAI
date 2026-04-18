# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Flask Web Application Module
Provides web interface and API endpoints, supporting real-time chat, configuration management, and scheduled task execution
"""

import os
import json
import queue
import threading
import time
import sys
import io
import uuid
import base64
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import wraps
from pycloudflared import try_cloudflare
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from agent import FranxAgent
import markdown
import bcrypt
import jwt
import secrets
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge import search, add_conversation

# Create Flask application instance
app = Flask(__name__)

# Startup timestamp for session validation
STARTUP_ID = str(int(time.time()))

# i18n directory path
I18N_DIR = Path(__file__).parent.parent / "i18n"

def load_config():
    """
    Load configuration file

    Returns:
        config dict
    """
    with open("./config.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """
    Save configuration file

    Args:
        config: config dict to save
    """
    with open("./config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# Setup Flask secret key from configuration
config = load_config()
if 'flask_secret_key' not in config:
    config['flask_secret_key'] = secrets.token_hex(32)
    save_config(config)
app.secret_key = config['flask_secret_key']

# Authentication helpers
PRIVATE_KEY_FILE = "private.key"
PUBLIC_KEY_FILE = "public.key"

def generate_rsa_keys():
    """Generate RSA key pair and save to files"""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    if os.name != 'nt':
        os.chmod(PRIVATE_KEY_FILE, 0o600)
    print("✅ Generated RSA key pair.")

def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key_pem():
    with open(PUBLIC_KEY_FILE, "r") as f:
        return f.read()

def generate_jwt_token():
    config = load_config()
    secret = config.get("jwt_secret")
    if not secret:
        secret = secrets.token_urlsafe(32)
        config["jwt_secret"] = secret
        save_config(config)
    expire_hours = 1
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + timedelta(hours=expire_hours),
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_jwt_token(token):
    config = load_config()
    secret = config.get("jwt_secret")
    if not secret:
        return False
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except jwt.InvalidTokenError:
        return False

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        config = load_config()
        # If no password has been set yet, allow access (frontend will guide setup)
        if "password_hash" not in config:
            return f(*args, **kwargs)
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_jwt_token(token):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# Initialize RSA keys on first run
if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
    generate_rsa_keys()

# Original global variables and functions
# Global variables: chat agent and task agent
chat_agent = None
chat_agent_lock = threading.Lock()  # Thread safety lock
tasks_agent = None
_public_url = None

# Start Cloudflare tunnel in a background thread and get the public URL
def start_cloudflare_tunnel():
    global _public_url
    try:
        # 1. Start a temporary tunnel
        tunnel = try_cloudflare(port=5000)
        
        # 2. Get the public address
        _public_url = tunnel
        print(f"✅ Cloudflare tunnel started: {_public_url.tunnel}")
    except Exception as e:
        print(f"❌ Failed to start Cloudflare tunnel: {e}")

# Scheduled task SSE broadcaster
class EventBroadcaster:
    def __init__(self):
        self.connections = []
        self.lock = threading.Lock()

    def subscribe(self):
        q = queue.Queue()
        with self.lock:
            self.connections.append(q)
        return q

    def unsubscribe(self, q):
        with self.lock:
            if q in self.connections:
                self.connections.remove(q)

    def broadcast(self, event_type, data):
        message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        with self.lock:
            for q in self.connections[:]:
                try:
                    q.put_nowait(message)
                except queue.Full:
                    pass

broadcaster = EventBroadcaster()

# Store cancellation events for running tasks
active_tasks = {}
active_tasks_lock = threading.Lock()

# Global dict for pending confirmations (used by /chat and /api/confirm_tool) 
_pending_confirmations = {}
_pending_lock = threading.Lock()

def init_agents():
    global chat_agent, tasks_agent, last_config_mtime
    config = load_config()
    last_config_mtime = os.path.getmtime("./config.json")
    
    temperature = config.get("temperature", 0.8)
    thinking = config.get("thinking", False)
    max_iterations = config.get("max_iterations", 100)
    threshold = config.get("threshold", 20)
    knowledge_k = config.get("knowledge_k", 5)
    
    settings = config.get("settings", "You are a helpful AI assistant.")
    
    # Chat agent
    chat_agent = FranxAgent(
        key=config["api_key"],
        url=config["base_url"],
        model=config["model"],
        settings=settings,
        max_iterations=max_iterations,
        temperature=temperature,
        thinking=thinking,
        threshold=threshold,
        knowledge_k=knowledge_k
    )
    
    # Task agent
    tasks_agent = FranxAgent(
        key=config["api_key"],
        url=config["base_url"],
        model=config["model"],
        settings=settings,
        max_iterations=max_iterations,
        temperature=temperature,
        thinking=thinking,
        threshold=threshold,
        knowledge_k=knowledge_k
    )

# Scheduled task execution function (supports cancellation and streaming)
def execute_task(task_id, content, cancel_event):
    """Execute a single scheduled task and push the process to SSE"""
    # Send start event
    broadcaster.broadcast('task_start', {
        'task_id': task_id,
        'content': content,
        'message': f"⏰ Executing scheduled task: {content}"
    })

    try:
        result_parts = []
        # Iterate generator, push each chunk in real time
        for chunk in tasks_agent.input(content):
            if cancel_event.is_set():
                broadcaster.broadcast('task_cancel', {'task_id': task_id})
                return
            result_parts.append(chunk)
            broadcaster.broadcast('task_chunk', {
                'task_id': task_id,
                'chunk': chunk
            })
        full_result = ''.join(result_parts)
        # Send completion event
        broadcaster.broadcast('task_done', {
            'task_id': task_id,
            'result': full_result
        })
    except Exception as e:
        broadcaster.broadcast('task_error', {
            'task_id': task_id,
            'error': str(e)
        })
    finally:
        with active_tasks_lock:
            if task_id in active_tasks:
                del active_tasks[task_id]

def run_tasks():
    """
    Scheduled task executor
    Checks tasks.json every 10 seconds and executes tasks matching the current time
    File format: {"HH:MM": "command content"}
    """
    # Initialize execution record set and last execution date
    if not hasattr(run_tasks, "_executed"):
        run_tasks._executed = set()
    if not hasattr(run_tasks, "_last_date"):
        run_tasks._last_date = None

    while True:
        # Check if task file exists
        if os.path.exists("./tasks.json"):
            try:
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            except:
                pass
            else:
                # Get current time
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                today = now.strftime("%Y-%m-%d")

                # If it's a new day, reset execution record
                if today != run_tasks._last_date:
                    run_tasks._executed.clear()
                    run_tasks._last_date = today

                # Iterate over all tasks (key is time, value is command)
                for time_str, content in tasks.items():
                    if time_str == current_time and time_str not in run_tasks._executed:
                        # Generate unique task ID
                        task_id = str(uuid.uuid4())
                        cancel_event = threading.Event()
                        with active_tasks_lock:
                            active_tasks[task_id] = cancel_event
                        # Start execution thread
                        thread = threading.Thread(target=execute_task, args=(task_id, content, cancel_event))
                        thread.daemon = True
                        thread.start()
                        run_tasks._executed.add(time_str)
        # Sleep 10 seconds before next check
        time.sleep(10)

# Start scheduled task thread
run_tasks_thread = threading.Thread(target=run_tasks, daemon=True)
run_tasks_thread.start()

# Authentication API endpoints
@app.route('/api/public-key', methods=['GET'])
def get_public_key():
    """Return RSA public key in PEM format"""
    return jsonify({'public_key': load_public_key_pem()})

@app.route('/api/setup', methods=['POST'])
def setup_password():
    """First-time password setup (RSA encrypted)"""
    config = load_config()
    if "password_hash" in config:
        return jsonify({'error': 'Password already set'}), 400
    data = request.get_json()
    encrypted_password = data.get('password')
    if not encrypted_password:
        return jsonify({'error': 'Missing password'}), 400
    private_key = load_private_key()
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        password = decrypted.decode()
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {e}'}), 400
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    config["password_hash"] = hashed.decode()
    if "jwt_secret" not in config:
        config["jwt_secret"] = secrets.token_urlsafe(32)
    save_config(config)
    token = generate_jwt_token()
    return jsonify({'status': 'success', 'token': token})

@app.route('/api/login', methods=['POST'])
def login():
    """Login and return JWT token"""
    config = load_config()
    if "password_hash" not in config:
        return jsonify({'error': 'Password not set'}), 400
    data = request.get_json()
    encrypted_password = data.get('password')
    if not encrypted_password:
        return jsonify({'error': 'Missing password'}), 400
    private_key = load_private_key()
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        password = decrypted.decode()
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {e}'}), 400
    stored_hash = config["password_hash"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        token = generate_jwt_token()
        return jsonify({'status': 'success', 'token': token})
    else:
        return jsonify({'error': 'Invalid password'}), 401

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if password is set and if current token is valid"""
    config = load_config()
    password_set = "password_hash" in config
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    valid = False
    if token and password_set:
        valid = verify_jwt_token(token)
    return jsonify({'password_set': password_set, 'authenticated': valid})

# i18n API endpoint
@app.route('/api/i18n', methods=['GET'])
def get_i18n():
    """
    Return i18n translations for the current language setting.
    Reads 'language' from config.json, falls back to 'en' if missing.
    Falls back to en.yaml if the specified language file does not exist.
    """
    try:
        config = load_config()
        lang = config.get("language", "en")
    except Exception:
        lang = "en"
    lang_file = I18N_DIR / f"{lang}.yaml"
    if not lang_file.exists():
        lang_file = I18N_DIR / "en.yaml"
    if not lang_file.exists():
        return jsonify({'language': 'en', 'translations': {}})
    with open(lang_file, 'r', encoding='utf-8') as f:
        translations = yaml.safe_load(f) or {}
    return jsonify({'language': lang, 'translations': translations})

@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    """Return current conversation messages for cross‑device sync"""
    if chat_agent is None:
        return jsonify({'error': 'Agent not initialized'}), 500
    # Return a copy to avoid accidental modification
    return jsonify({'messages': chat_agent.messages.copy()})

@app.route('/api/save_partial', methods=['POST'])
@login_required
def save_partial():
    """
    Save a partially generated response when the user stops the generation.
    This ensures that the already streamed content is persisted in the conversation history and vector memory, enabling cross‑device sync and long‑term recall.
    """
    if chat_agent is None:
        return jsonify({'error': 'Agent not initialized'}), 500

    data = request.get_json()
    user_message = data.get('user_message')
    partial_response = data.get('partial_response')

    if not user_message or not partial_response:
        return jsonify({'error': 'Missing user_message or partial_response'}), 400

    # Append the partial assistant message to the in‑memory conversation history
    assistant_message = {"role": "assistant", "content": partial_response}
    chat_agent.messages.append(assistant_message)

    # Save to vector database and memories directory (backup)
    add_conversation(user_message, partial_response)

    # Trigger memory compression to keep context length under control
    chat_agent.memory()

    return jsonify({'status': 'ok'})

# Tool confirmation API
@app.route('/api/confirm_tool', methods=['POST'])
@login_required
def confirm_tool():
    """
    Receive user's decision for a pending tool confirmation and resume the agent generator.
    """
    data = request.get_json()
    confirm_id = data.get('confirm_id')
    approved = data.get('approved', False)

    if not confirm_id:
        return jsonify({'error': 'Missing confirm_id'}), 400

    with _pending_lock:
        if confirm_id not in _pending_confirmations:
            return jsonify({'error': 'Invalid or expired confirm_id'}), 404
        # Retrieve the pending info
        pending = _pending_confirmations.pop(confirm_id)

    pending['result']['done'] = approved  # Store the decision
    pending['event'].set()  # Wake up the loop

    return jsonify({'status': 'ok'})

# Frontend routes
@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Register page (first-time password setup)"""
    return render_template('register.html')

@app.route('/')
def index():
    """
    Root route
    Returns web chat interface template

    Returns:
        Rendered HTML page
    """
    return render_template('index.html')

@app.route('/session', methods=['GET'])
def get_session():
    """
    Get session ID
    For frontend to validate session validity

    Returns:
        JSON response containing startup_id
    """
    return jsonify({'startup_id': STARTUP_ID})

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    def generate():
        # Save original stdout
        old_stdout = sys.stdout
        # Buffer for compatibility (not actually sent)
        sio = io.StringIO()
        # Queue for real-time logs (from print statements)
        log_q = queue.Queue()

        # Custom output stream: each print writes to both original buffer and real-time queue
        class QueueStream(io.TextIOBase):
            def write(self, s):
                if s:
                    log_q.put(s)
                return sio.write(s)

        # Redirect stdout to custom stream
        sys.stdout = QueueStream()

        # Accumulate full response (for final HTML)
        full_response = ""

        try:
            # Retrieve knowledge and send to frontend
            try:
                # Get knowledge_k from agent, default to 5 if not present
                k = getattr(chat_agent, 'knowledge_k', 5)
                relevant = search(user_message, k=k)
                for item in relevant:
                    # Send each knowledge item as a separate 'knowledge' event
                    yield f"data: {json.dumps({'type': 'knowledge', 'text': item})}\n\n"
            except Exception as e:
                # Retrieval failure does not affect main flow, only print log
                print(f"Knowledge retrieval failed: {e}")

            # Get the generator from agent (this yields text and confirmation requests)
            agent_gen = chat_agent.input(user_message)
            gen_exhausted = False

            while not gen_exhausted:
                # Drain log queue (print output)
                while True:
                    try:
                        line = log_q.get_nowait()
                        if line:
                            yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                    except queue.Empty:
                        break

                try:
                    # Get next item from agent generator
                    item = next(agent_gen)
                except StopIteration:
                    # Generator finished
                    gen_exhausted = True
                    break

                # Handle different types of items
                if isinstance(item, str):
                    # Normal text chunk
                    full_response += item
                    yield f"data: {json.dumps({'type': 'content', 'text': item})}\n\n"
                elif isinstance(item, dict) and item.get('type') == 'confirmation_required':
                    # Confirmation request
                    confirm_id = item['confirm_id']
                    # Create an event and result holder to wait for user decision
                    event = threading.Event()
                    result_holder = {'done': None}  # None means not decided yet
                    # Store in global dict
                    with _pending_lock:
                        _pending_confirmations[confirm_id] = {
                            'generator': agent_gen,
                            'event': event,
                            'result': result_holder,
                            'tool_name': item['tool_name'],
                            'arguments': item['arguments']
                        }
                    # Send confirmation request to frontend
                    yield f"data: {json.dumps(item)}\n\n"
                    # Wait for the confirmation API to set the result
                    event.wait()
                    
                    # Now we resume the generator here
                    approved = result_holder.get('done', False)
                    try:
                        # generator.send() returns the next yielded value (tool_result)
                        next_item = agent_gen.send(approved)
                        
                        # Forward the yielded item to frontend
                        if isinstance(next_item, dict):
                             yield f"data: {json.dumps(next_item)}\n\n"
                        elif isinstance(next_item, str):
                             # Handle text if returned immediately
                             full_response += next_item
                             yield f"data: {json.dumps({'type': 'content', 'text': next_item})}\n\n"
                    except StopIteration:
                        gen_exhausted = True
                    
                    continue  # Go back to the loop to get next items
                elif isinstance(item, dict) and item.get('type') == 'tool_call':
                    # Structured tool call event
                    yield f"data: {json.dumps(item)}\n\n"
                
                # Handle tool result event
                elif isinstance(item, dict) and item.get('type') == 'tool_result':
                    # Tool result event
                    yield f"data: {json.dumps(item)}\n\n"
                
                else:
                    # Unknown item type, ignore
                    print(f"Unknown item from agent generator: {item}")

            # Final drain of logs
            while True:
                try:
                    line = log_q.get_nowait()
                    if line:
                        yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                except queue.Empty:
                    break

            # Render full message as HTML (backend rendering)
            if full_response:
                try:
                    # Convert Markdown to HTML using markdown library
                    html = markdown.markdown(full_response, extensions=['tables', 'fenced_code'])
                    yield f"data: {json.dumps({'type': 'html', 'html': html})}\n\n"
                except Exception as e:
                    # Rendering failed, send error but don't interrupt stream
                    yield f"data: {json.dumps({'type': 'error', 'text': f'Markdown rendering failed: {str(e)}'})}\n\n"

            # Send stream end signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Store the current Q&A pair into the vector database
            if full_response:
                add_conversation(user_message, full_response)

        except Exception as e:
            # Catch any unhandled exceptions to prevent server crash
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'text': f'Agent crashed: {str(e)}'})}\n\n"
        finally:
            # CRITICAL: MUST restore stdout no matter what happens
            sys.stdout = old_stdout

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

@app.route('/config', methods=['GET'])
@login_required
def get_config():
    """
    Get configuration interface
    Returns current configuration (excluding sensitive info like API keys)

    Returns:
        JSON response of config dict
    """
    try:
        with open("./config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config', methods=['POST'])
@login_required
def update_config():
    """
    Update configuration interface
    Save configuration and reinitialize agents

    Returns:
        JSON response of operation status or error message
    """
    data = request.get_json()
    required = ['api_key', 'base_url', 'model']
    # Check required fields exist
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    try:
        # Save configuration file
        with open("./config.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Reinitialize agents
        init_agents()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Scheduled task management API
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks_api():
    """
    Scheduled task management API
    - GET: return all tasks
    - POST: add or delete tasks, distinguished by action parameter
        action=add: add task, requires time and content
        action=delete: delete task, requires time
    """
    if request.method == 'GET':
        try:
            if os.path.exists("./tasks.json"):
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            else:
                tasks = {}
            return jsonify(tasks)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        if action == 'add':
            time_str = data.get('time')
            content = data.get('content')
            if not time_str or not content:
                return jsonify({'error': 'Missing time or content field'}), 400
            try:
                if os.path.exists("./tasks.json"):
                    with open("./tasks.json", 'r', encoding='utf-8') as f:
                        tasks = json.load(f)
                else:
                    tasks = {}
                tasks[time_str] = content
                with open("./tasks.json", 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)
                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        elif action == 'delete':
            time_str = data.get('time')
            if not time_str:
                return jsonify({'error': 'Missing time field'}), 400
            try:
                if not os.path.exists("./tasks.json"):
                    return jsonify({'error': 'Task file does not exist'}), 404
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                if time_str in tasks:
                    del tasks[time_str]
                    with open("./tasks.json", 'w', encoding='utf-8') as f:
                        json.dump(tasks, f, indent=2, ensure_ascii=False)
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Task does not exist'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Unknown action'}), 400

# SSE event stream
@app.route('/events')
@login_required
def events():
    """Server-Sent Events endpoint for pushing scheduled task real-time status"""
    def generate():
        q = broadcaster.subscribe()
        try:
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield msg
                except queue.Empty:
                    yield ": heartbeat\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

# Cancel task API
@app.route('/cancel_task/<task_id>', methods=['POST'])
@login_required
def cancel_task(task_id):
    """Cancel a running task"""
    with active_tasks_lock:
        if task_id in active_tasks:
            active_tasks[task_id].set()
            return jsonify({'status': 'cancelling'})
        else:
            return jsonify({'error': 'Task does not exist or has already ended'}), 404

if __name__ == '__main__':
    # Initialize agents
    init_agents()
    # Start Cloudflare tunnel in a background thread
    tunnel_thread = threading.Thread(target=start_cloudflare_tunnel, daemon=True)
    tunnel_thread.start()
    # Start web service (127.0.0.1:5000, debug=False to avoid production risks)
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)