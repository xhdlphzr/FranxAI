# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Chat Route - /chat SSE stream
"""

import json
import queue
import sys
import io
import threading
import markdown
from flask import Blueprint, request, jsonify, Response, stream_with_context
from src.auth import login_required
from src import state
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from knowledge import search, add_conversation

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    def generate():
        old_stdout = sys.stdout
        sio = io.StringIO()
        log_q = queue.Queue()

        class QueueStream(io.TextIOBase):
            def write(self, s):
                if s:
                    log_q.put(s)
                return sio.write(s)

        sys.stdout = QueueStream()
        full_response = ""

        try:
            try:
                k = getattr(state.chat_agent, 'knowledge_k', 5)
                relevant = search(user_message, k=k)
                for item in relevant:
                    yield f"data: {json.dumps({'type': 'knowledge', 'text': item})}\n\n"
            except Exception as e:
                print(f"Knowledge retrieval failed: {e}")

            agent_gen = state.chat_agent.input(user_message)
            gen_exhausted = False

            while not gen_exhausted:
                while True:
                    try:
                        line = log_q.get_nowait()
                        if line:
                            yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                    except queue.Empty:
                        break

                try:
                    item = next(agent_gen)
                except StopIteration:
                    gen_exhausted = True
                    break

                if isinstance(item, str):
                    full_response += item
                    yield f"data: {json.dumps({'type': 'content', 'text': item})}\n\n"
                elif isinstance(item, dict) and item.get('type') == 'confirmation_required':
                    confirm_id = item['confirm_id']
                    event = threading.Event()
                    result_holder = {'done': None}
                    with state.pending_lock:
                        state.pending_confirmations[confirm_id] = {
                            'generator': agent_gen,
                            'event': event,
                            'result': result_holder,
                            'tool_name': item['tool_name'],
                            'arguments': item['arguments']
                        }
                    yield f"data: {json.dumps(item)}\n\n"
                    event.wait()
                    approved = result_holder.get('done', False)
                    try:
                        next_item = agent_gen.send(approved)
                        if isinstance(next_item, dict):
                            yield f"data: {json.dumps(next_item)}\n\n"
                        elif isinstance(next_item, str):
                            full_response += next_item
                            yield f"data: {json.dumps({'type': 'content', 'text': next_item})}\n\n"
                    except StopIteration:
                        gen_exhausted = True
                    continue
                elif isinstance(item, dict) and item.get('type') == 'tool_call':
                    yield f"data: {json.dumps(item)}\n\n"
                elif isinstance(item, dict) and item.get('type') == 'tool_result':
                    yield f"data: {json.dumps(item)}\n\n"
                else:
                    print(f"Unknown item from agent generator: {item}")

            while True:
                try:
                    line = log_q.get_nowait()
                    if line:
                        yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                except queue.Empty:
                    break

            if full_response:
                try:
                    html = markdown.markdown(full_response, extensions=['tables', 'fenced_code'])
                    yield f"data: {json.dumps({'type': 'html', 'html': html})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'text': f'Markdown rendering failed: {str(e)}'})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            if full_response:
                add_conversation(user_message, full_response)

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'text': f'Agent crashed: {str(e)}'})}\n\n"
        finally:
            sys.stdout = old_stdout

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )