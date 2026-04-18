# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Config Routes - /config, /api/messages, /api/save_partial, /api/confirm_tool
"""

import json
from flask import Blueprint, request, jsonify
from src.auth import login_required
from src import state
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from knowledge import add_conversation

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    if state.chat_agent is None:
        return jsonify({'error': 'Agent not initialized'}), 500
    return jsonify({'messages': state.chat_agent.messages.copy()})


@config_bp.route('/api/save_partial', methods=['POST'])
@login_required
def save_partial():
    if state.chat_agent is None:
        return jsonify({'error': 'Agent not initialized'}), 500

    data = request.get_json()
    user_message = data.get('user_message')
    partial_response = data.get('partial_response')

    if not user_message or not partial_response:
        return jsonify({'error': 'Missing user_message or partial_response'}), 400

    assistant_message = {"role": "assistant", "content": partial_response}
    state.chat_agent.messages.append(assistant_message)

    add_conversation(user_message, partial_response)

    state.chat_agent.memory()

    return jsonify({'status': 'ok'})


@config_bp.route('/api/confirm_tool', methods=['POST'])
@login_required
def confirm_tool():
    data = request.get_json()
    confirm_id = data.get('confirm_id')
    approved = data.get('approved', False)

    if not confirm_id:
        return jsonify({'error': 'Missing confirm_id'}), 400

    with state.pending_lock:
        if confirm_id not in state.pending_confirmations:
            return jsonify({'error': 'Invalid or expired confirm_id'}), 404
        pending = state.pending_confirmations.pop(confirm_id)

    pending['result']['done'] = approved
    pending['event'].set()

    return jsonify({'status': 'ok'})


@config_bp.route('/config', methods=['GET'])
@login_required
def get_config():
    try:
        with open("./config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@config_bp.route('/config', methods=['POST'])
@login_required
def update_config():
    data = request.get_json()
    required = ['api_key', 'base_url', 'model']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    try:
        with open("./config.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Lazy import to avoid circular dependency | 延迟导入避免循环依赖
        from src.app import init_agents
        init_agents()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500