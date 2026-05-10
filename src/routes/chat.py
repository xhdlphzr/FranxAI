# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Chat Route - /chat SSE stream
"""

import json
import queue
import sys
import io
import uuid
import markdown
from flask import Blueprint, request, jsonify, Response, stream_with_context
from src.auth import login_required
from src import state
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from knowledge import search, add_conversation

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

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
            # Knowledge retrieval
            try:
                k = getattr(state.chat_agent, "knowledge_k", 5)
                relevant = search(user_message, k=k)
                for item in relevant:
                    yield f"data: {json.dumps({'type': 'knowledge', 'text': item})}\n\n"
            except Exception as e:
                print(f"Knowledge retrieval failed: {e}")

            agent_gen = state.chat_agent.input(user_message)
            gen_exhausted = False

            while not gen_exhausted:
                # Flush logs
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

                # Text content chunk
                if isinstance(item, str):
                    full_response += item
                    yield f"data: {json.dumps({'type': 'content', 'text': item})}\n\n"

                # Tool call event
                elif isinstance(item, dict) and item.get("type") == "tool_call":
                    yield f"data: {json.dumps(item)}\n\n"

                # Tool result event
                elif isinstance(item, dict) and item.get("type") == "tool_result":
                    yield f"data: {json.dumps(item)}\n\n"

                # Confirmation request – wait for user approval instead of auto‑approving
                elif (
                    isinstance(item, dict)
                    and item.get("type") == "confirmation_required"
                ):
                    confirm_id = item.get("confirm_id", str(uuid.uuid4()))
                    # Ensure the item carries the confirm_id so the frontend can use it
                    item["confirm_id"] = confirm_id

                    # Send the confirmation request to the frontend
                    yield f"data: {json.dumps(item)}\n\n"

                    # Create a queue to wait for the user's decision
                    confirm_queue = queue.Queue()

                    with state.pending_lock:
                        state.pending_confirmations[confirm_id] = {
                            "generator": agent_gen,
                            "queue": confirm_queue,
                        }

                    # Block until the user approves or rejects via /api/confirm_tool
                    try:
                        approved = confirm_queue.get()
                    except queue.Empty:
                        approved = False  # Treat timeout as rejection

                    with state.pending_lock:
                        state.pending_confirmations.pop(confirm_id, None)

                    # Feed the user's decision back into the generator
                    try:
                        next_item = agent_gen.send(approved)
                        if isinstance(next_item, dict):
                            if next_item.get("type") == "tool_result":
                                yield f"data: {json.dumps(next_item)}\n\n"
                            else:
                                # In case something else comes back, send it as generic
                                yield f"data: {json.dumps(next_item)}\n\n"
                        elif isinstance(next_item, str):
                            full_response += next_item
                            yield f"data: {json.dumps({'type': 'content', 'text': next_item})}\n\n"
                    except StopIteration:
                        gen_exhausted = True

                else:
                    print(f"Unknown item from agent generator: {item}")

            # Final flush of logs
            while True:
                try:
                    line = log_q.get_nowait()
                    if line:
                        yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                except queue.Empty:
                    break

            # Markdown rendering for full response
            if full_response:
                try:
                    html = markdown.markdown(
                        full_response, extensions=["tables", "fenced_code"]
                    )
                    yield f"data: {json.dumps({'type': 'html', 'html': html})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'text': f'Markdown rendering failed: {str(e)}'})}\n\n"

            # Conversation history
            if full_response:
                add_conversation(user_message, full_response)

            # Done signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except GeneratorExit:
            # Client disconnected – clean up any pending confirmations
            with state.pending_lock:
                for confirm_id, info in list(state.pending_confirmations.items()):
                    if info.get("generator") is agent_gen:
                        # Wake up the generator to let it finish gracefully
                        try:
                            info["queue"].put(
                                False
                            )  # Wake up from waiting so that the generator can finish
                        except Exception:
                            pass
                        del state.pending_confirmations[confirm_id]
        except Exception as e:
            import traceback

            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'text': f'Agent crashed: {str(e)}'})}\n\n"
        finally:
            sys.stdout = old_stdout

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chat_bp.route("/api/confirm_tool", methods=["POST"])
@login_required
def confirm_tool():
    """
    Called by the frontend when the user clicks Approve or Reject.
    Wakes up the blocked generator in /chat.
    """
    data = request.get_json()
    confirm_id = data.get("confirm_id")
    approved = data.get("approved", False)

    if not confirm_id:
        return jsonify({"error": "Missing confirm_id"}), 400

    with state.pending_lock:
        info = state.pending_confirmations.get(confirm_id)
        if info and "queue" in info:
            info["queue"].put(approved)
            return jsonify({"status": "ok"})

    return jsonify({"error": "No pending confirmation found for this id"}), 404
