# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Flask Application - Assembly, startup, frontend routes
"""

import secrets
import time
import threading
import sys
from pathlib import Path

from flask import Flask, render_template, jsonify
from pycloudflared import try_cloudflare

# Add project root for src.* and knowledge imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import FranxAgent
from src.state import load_config, save_config
from src.routes.auth import auth_bp
from src.routes.chat import chat_bp
from src.routes.config import config_bp
from src.routes.tasks import tasks_bp
# Import scheduler to start its background thread
from src import scheduler

app = Flask(__name__)
STARTUP_ID = str(int(time.time()))

# Setup Flask secret key
config = load_config()
if 'flask_secret_key' not in config:
    config['flask_secret_key'] = secrets.token_hex(32)
    save_config(config)
app.secret_key = config['flask_secret_key']

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(config_bp)
app.register_blueprint(tasks_bp)

_public_url = None


def start_cloudflare_tunnel():
    global _public_url
    try:
        tunnel = try_cloudflare(port=5000)
        _public_url = tunnel
        print(f"✅ Cloudflare tunnel started: {_public_url.tunnel}")
    except Exception as e:
        print(f"❌ Failed to start Cloudflare tunnel: {e}")


def init_agents():
    from src import state
    config = load_config()

    temperature = config.get("temperature", 0.8)
    thinking = config.get("thinking", False)
    max_iterations = config.get("max_iterations", 100)
    threshold = config.get("threshold", 20)
    knowledge_k = config.get("knowledge_k", 5)
    settings = config.get("settings", "You are a helpful AI assistant.")

    state.chat_agent = FranxAgent(
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

    state.tasks_agent = FranxAgent(
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


# Frontend routes
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/session', methods=['GET'])
def get_session():
    return jsonify({'startup_id': STARTUP_ID})


if __name__ == '__main__':
    init_agents()
    tunnel_thread = threading.Thread(target=start_cloudflare_tunnel, daemon=True)
    tunnel_thread.start()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)