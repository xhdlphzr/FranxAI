# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Tasks Routes - /tasks, /events, /cancel_task
"""

import os
import json
import queue
from flask import Blueprint, request, jsonify, Response, stream_with_context
from src.auth import login_required
from src.scheduler import broadcaster, active_tasks, active_tasks_lock

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks_api():
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


@tasks_bp.route('/events')
@login_required
def events():
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
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@tasks_bp.route('/cancel_task/<task_id>', methods=['POST'])
@login_required
def cancel_task(task_id):
    with active_tasks_lock:
        if task_id in active_tasks:
            active_tasks[task_id].set()
            return jsonify({'status': 'cancelling'})
        else:
            return jsonify({'error': 'Task does not exist or has already ended'}), 404