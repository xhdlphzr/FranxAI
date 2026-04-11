# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
Flask Web Application Module | Flask Web应用模块
Provides web interface and API endpoints, supporting real-time chat, configuration management, and scheduled task execution | 提供Web界面和API接口，支持实时聊天、配置管理和定时任务执行
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
from agent import FranxAI
import markdown
import bcrypt
import jwt
import secrets
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge import search, add_conversation

# Create Flask application instance | 创建Flask应用实例
app = Flask(__name__)

# Startup timestamp for session validation | 启动时的时间戳，用于会话验证
STARTUP_ID = str(int(time.time()))

def load_config():
    """
    Load configuration file | 加载配置文件

    Returns:
        config dict | 配置字典
    """
    with open("./config.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """
    Save configuration file | 保存配置文件

    Args:
        config: config dict to save | 要保存的配置字典
    """
    with open("./config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# Setup Flask secret key from configuration | 从配置文件设置 Flask 密钥
config = load_config()
if 'flask_secret_key' not in config:
    config['flask_secret_key'] = secrets.token_hex(32)
    save_config(config)
app.secret_key = config['flask_secret_key']

# Authentication helpers | 认证辅助函数
PRIVATE_KEY_FILE = "private.key"
PUBLIC_KEY_FILE = "public.key"

def generate_rsa_keys():
    """Generate RSA key pair and save to files | 生成 RSA 密钥对并保存到文件"""
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
    print("✅ Generated RSA key pair. | 已生成 RSA 密钥对。")

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
    """Decorator to protect routes that require authentication | 保护需要认证的路由的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        config = load_config()
        # If no password has been set yet, allow access (frontend will guide setup) | 如果尚未设置密码，允许访问（前端会引导设置）
        if "password_hash" not in config:
            return f(*args, **kwargs)
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_jwt_token(token):
            return jsonify({'error': 'Unauthorized | 未授权'}), 401
        return f(*args, **kwargs)
    return decorated

# Initialize RSA keys on first run | 首次运行时生成 RSA 密钥对
if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
    generate_rsa_keys()

# Original global variables and functions | 原始全局变量和函数
# Global variables: chat agent and task agent | 全局变量：聊天智能体和任务智能体
chat_agent = None
chat_agent_lock = threading.Lock()  # Thread safety lock | 用于线程安全的锁
tasks_agent = None
_public_url = None

# Start Cloudflare tunnel in a background thread and get the public URL | 在后台线程中启动 Cloudflare 隧道并获取公网 URL
def start_cloudflare_tunnel():
    """Start a Cloudflare tunnel in a background thread and get the public URL | 在后台线程中启动 Cloudflare 隧道并获取公网 URL"""
    global _public_url
    try:
        # 1. Start a temporary tunnel | 1. 启动临时隧道
        tunnel = try_cloudflare(port=5000)
        
        # 2. Get the public address | 2. 获取公网地址
        _public_url = tunnel
        print(f"✅ Cloudflare tunnel started | Cloudflare隧道已启动：{_public_url.tunnel}")
    except Exception as e:
        print(f"❌ Failed to start Cloudflare tunnel | 启动Cloudflare隧道失败：{e}")

# Scheduled task SSE broadcaster | 定时任务 SSE 广播器
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

# Store cancellation events for running tasks | 存储正在执行的任务取消事件
active_tasks = {}
active_tasks_lock = threading.Lock()

# Global dict for pending confirmations (used by /chat and /api/confirm_tool) | 全局待确认字典（用于 /chat 和 /api/confirm_tool）
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
    
    settings = config.get("settings", "You are a helpful AI assistant. 你是一个有用的AI助手。")
    
    # Chat agent | 聊天智能体
    chat_agent = FranxAI(
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
    
    # Task agent | 任务智能体
    tasks_agent = FranxAI(
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

# Scheduled task execution function (supports cancellation and streaming) | 定时任务执行函数（支持取消和流式推送）
def execute_task(task_id, content, cancel_event):
    """Execute a single scheduled task and push the process to SSE | 执行单个定时任务，并将过程实时推送到 SSE"""
    # Send start event | 发送开始事件
    broadcaster.broadcast('task_start', {
        'task_id': task_id,
        'content': content,
        'message': f"⏰ Executing scheduled task: {content} | ⏰ 执行定时任务: {content}"
    })

    try:
        result_parts = []
        # Iterate generator, push each chunk in real time | 迭代生成器，实时推送每个 chunk
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
        # Send completion event | 发送完成事件
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
    Scheduled task executor | 定时任务执行器
    Checks tasks.json every 10 seconds and executes tasks matching the current time | 每隔10秒检查一次tasks.json，执行当前时间对应的任务
    File format: {"HH:MM": "command content"} | 文件格式：{"HH:MM": "命令内容"}
    """
    # Initialize execution record set and last execution date | 初始化执行记录集合和上次执行日期
    if not hasattr(run_tasks, "_executed"):
        run_tasks._executed = set()
    if not hasattr(run_tasks, "_last_date"):
        run_tasks._last_date = None

    while True:
        # Check if task file exists | 检查任务文件是否存在
        if os.path.exists("./tasks.json"):
            try:
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            except:
                pass
            else:
                # Get current time | 获取当前时间
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                today = now.strftime("%Y-%m-%d")

                # If it's a new day, reset execution record | 如果是新的一天，重置执行记录
                if today != run_tasks._last_date:
                    run_tasks._executed.clear()
                    run_tasks._last_date = today

                # Iterate over all tasks (key is time, value is command) | 遍历所有任务（键为时间，值为命令）
                for time_str, content in tasks.items():
                    if time_str == current_time and time_str not in run_tasks._executed:
                        # Generate unique task ID | 生成唯一任务ID
                        task_id = str(uuid.uuid4())
                        cancel_event = threading.Event()
                        with active_tasks_lock:
                            active_tasks[task_id] = cancel_event
                        # Start execution thread | 启动执行线程
                        thread = threading.Thread(target=execute_task, args=(task_id, content, cancel_event))
                        thread.daemon = True
                        thread.start()
                        run_tasks._executed.add(time_str)
        # Sleep 10 seconds before next check | 睡眠10秒后再次检查
        time.sleep(10)

# Start scheduled task thread | 启动定时任务线程
run_tasks_thread = threading.Thread(target=run_tasks, daemon=True)
run_tasks_thread.start()

# Authentication API endpoints | 认证 API 端点
@app.route('/api/public-key', methods=['GET'])
def get_public_key():
    """Return RSA public key in PEM format | 返回 PEM 格式的 RSA 公钥"""
    return jsonify({'public_key': load_public_key_pem()})

@app.route('/api/setup', methods=['POST'])
def setup_password():
    """First-time password setup (RSA encrypted) | 首次设置密码（RSA 加密传输）"""
    config = load_config()
    if "password_hash" in config:
        return jsonify({'error': 'Password already set | 密码已设置'}), 400
    data = request.get_json()
    encrypted_password = data.get('password')
    if not encrypted_password:
        return jsonify({'error': 'Missing password | 缺少密码'}), 400
    private_key = load_private_key()
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        password = decrypted.decode()
    except Exception as e:
        return jsonify({'error': f'Decryption failed | 解密失败: {e}'}), 400
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    config["password_hash"] = hashed.decode()
    if "jwt_secret" not in config:
        config["jwt_secret"] = secrets.token_urlsafe(32)
    save_config(config)
    token = generate_jwt_token()
    return jsonify({'status': 'success', 'token': token})

@app.route('/api/login', methods=['POST'])
def login():
    """Login and return JWT token | 登录并返回 JWT token"""
    config = load_config()
    if "password_hash" not in config:
        return jsonify({'error': 'Password not set | 密码未设置'}), 400
    data = request.get_json()
    encrypted_password = data.get('password')
    if not encrypted_password:
        return jsonify({'error': 'Missing password | 缺少密码'}), 400
    private_key = load_private_key()
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        password = decrypted.decode()
    except Exception as e:
        return jsonify({'error': f'Decryption failed | 解密失败: {e}'}), 400
    stored_hash = config["password_hash"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        token = generate_jwt_token()
        return jsonify({'status': 'success', 'token': token})
    else:
        return jsonify({'error': 'Invalid password | 密码错误'}), 401

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if password is set and if current token is valid | 检查密码是否已设置以及当前 token 是否有效"""
    config = load_config()
    password_set = "password_hash" in config
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    valid = False
    if token and password_set:
        valid = verify_jwt_token(token)
    return jsonify({'password_set': password_set, 'authenticated': valid})

@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    """Return current conversation messages for cross‑device sync | 返回当前对话消息用于跨设备同步"""
    if chat_agent is None:
        return jsonify({'error': 'Agent not initialized'}), 500
    # Return a copy to avoid accidental modification | 返回副本以避免意外修改
    return jsonify({'messages': chat_agent.messages.copy()})

@app.route('/api/save_partial', methods=['POST'])
@login_required
def save_partial():
    """
    Save a partially generated response when the user stops the generation. | 当用户停止生成时保存部分回复内容。
    This ensures that the already streamed content is persisted in the conversation history and vector memory, enabling cross‑device sync and long‑term recall. | 确保已流式输出的内容被持久化到对话历史和向量记忆，从而实现跨设备同步和长期回忆。
    """
    if chat_agent is None:
        return jsonify({'error': 'Agent not initialized'}), 500

    data = request.get_json()
    user_message = data.get('user_message')
    partial_response = data.get('partial_response')

    if not user_message or not partial_response:
        return jsonify({'error': 'Missing user_message or partial_response'}), 400

    # Append the partial assistant message to the in‑memory conversation history | 将部分助手消息追加到内存中的对话历史
    assistant_message = {"role": "assistant", "content": partial_response}
    chat_agent.messages.append(assistant_message)

    # Save to vector database and memories directory (backup) | 保存到向量数据库和 memories 目录（备份）
    add_conversation(user_message, partial_response)

    # Trigger memory compression to keep context length under control | 触发记忆压缩以控制上下文长度
    chat_agent.memory()

    return jsonify({'status': 'ok'})

# Tool confirmation API | 工具确认 API
@app.route('/api/confirm_tool', methods=['POST'])
@login_required
def confirm_tool():
    """
    Receive user's decision for a pending tool confirmation and resume the agent generator.
    | 接收用户对等待中的工具确认的决策，并恢复智能体生成器。
    """
    data = request.get_json()
    confirm_id = data.get('confirm_id')
    approved = data.get('approved', False)

    if not confirm_id:
        return jsonify({'error': 'Missing confirm_id'}), 400

    with _pending_lock:
        if confirm_id not in _pending_confirmations:
            return jsonify({'error': 'Invalid or expired confirm_id'}), 404
        # Retrieve the pending info | 获取待确认信息
        pending = _pending_confirmations.pop(confirm_id)
        generator = pending['generator']
        event = pending['event']
        result_holder = pending['result']

    # Send the user's decision back to the generator | 将用户决策发送回生成器
    try:
        # Resume the generator with the approval status | 使用批准状态恢复生成器
        generator.send(approved)
    except StopIteration:
        # Generator finished (should not happen) | 生成器已结束（不应发生）
        pass
    finally:
        # Signal that the response has been set | 通知等待线程已收到结果
        result_holder['done'] = True
        event.set()

    return jsonify({'status': 'ok'})

# Frontend routes | 前端路由
@app.route('/login')
def login_page():
    """Login page | 登录页面"""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Register page (first-time password setup) | 注册页面（首次设置密码）"""
    return render_template('register.html')

@app.route('/')
def index():
    """
    Root route | 根路径路由
    Returns web chat interface template | 返回Web聊天界面模板

    Returns:
        Rendered HTML page | 渲染后的HTML页面
    """
    return render_template('index.html')

@app.route('/session', methods=['GET'])
def get_session():
    """
    Get session ID | 获取会话ID
    For frontend to validate session validity | 用于前端验证会话是否有效

    Returns:
        JSON response containing startup_id | 包含startup_id的JSON响应
    """
    return jsonify({'startup_id': STARTUP_ID})

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty | 消息不能为空'}), 400

    def generate():
        # Save original stdout | 保存原始标准输出
        old_stdout = sys.stdout
        # Buffer for compatibility (not actually sent) | 用于兼容原逻辑的缓冲区（实际不再发送，仅用于写入）
        sio = io.StringIO()
        # Queue for real-time logs (from print statements) | 实时日志队列（来自 print 语句）
        log_q = queue.Queue()

        # Custom output stream: each print writes to both original buffer and real-time queue | 自定义输出流：每个 print 同时写入原缓冲区和实时队列
        class QueueStream(io.TextIOBase):
            def write(self, s):
                if s:
                    log_q.put(s)
                return sio.write(s)

        # Redirect stdout to custom stream | 重定向标准输出到自定义流
        sys.stdout = QueueStream()

        # Accumulate full response (for final HTML) | 累积完整回复（用于最终 HTML）
        full_response = ""

        # Retrieve knowledge and send to frontend | 检索知识并发送到前端
        try:
            # Get knowledge_k from agent, default to 5 if not present | 从 agent 获取 knowledge_k，如果不存在则默认 5
            k = getattr(chat_agent, 'knowledge_k', 5)
            relevant = search(user_message, k=k)
            for item in relevant:
                # Send each knowledge item as a separate 'knowledge' event | 每条知识单独发送一个 knowledge 事件
                yield f"data: {json.dumps({'type': 'knowledge', 'text': item})}\n\n"
        except Exception as e:
            # Retrieval failure does not affect main flow, only print log | 检索失败不影响主流程，仅打印日志
            print(f"Knowledge retrieval failed | 知识检索失败: {e}")

        # Get the generator from agent (this yields text and confirmation requests) | 获取智能体的生成器（yield 文本和确认请求）
        agent_gen = chat_agent.input(user_message)
        gen_exhausted = False

        while not gen_exhausted:
            # Drain log queue (print output) | 排空日志队列
            while True:
                try:
                    line = log_q.get_nowait()
                    if line:
                        yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                except queue.Empty:
                    break

            try:
                # Get next item from agent generator | 从智能体生成器获取下一个项目
                item = next(agent_gen)
            except StopIteration:
                # Generator finished | 生成器结束
                gen_exhausted = True
                break

            # Handle different types of items | 处理不同类型的项目
            if isinstance(item, str):
                # Normal text chunk | 普通文本块
                full_response += item
                yield f"data: {json.dumps({'type': 'content', 'text': item})}\n\n"
            elif isinstance(item, dict) and item.get('type') == 'confirmation_required':
                # Confirmation request | 确认请求
                confirm_id = item['confirm_id']
                # Create an event and result holder to wait for user decision | 创建事件和结果容器以等待用户决策
                event = threading.Event()
                result_holder = {'done': False}
                # Store in global dict | 存储到全局字典
                with _pending_lock:
                    _pending_confirmations[confirm_id] = {
                        'generator': agent_gen,
                        'event': event,
                        'result': result_holder,
                        'tool_name': item['tool_name'],
                        'arguments': item['arguments']
                    }
                # Send confirmation request to frontend | 发送确认请求到前端
                yield f"data: {json.dumps(item)}\n\n"
                # Wait for the confirmation API to set the result | 等待确认 API 设置结果
                # Note: This blocks the current thread until the user responds via /api/confirm_tool | 注意：这会阻塞当前线程，直到用户通过 /api/confirm_tool 响应
                event.wait()
                # After waiting, the generator already received .send(approved) and continues | 等待结束后，生成器已经通过 .send(approved) 继续执行
                continue  # Go back to the loop to get next items after confirmation | 回到循环，获取确认后的后续项目
            else:
                # Unknown item type, ignore | 未知类型，忽略
                print(f"Unknown item from agent generator: {item}")

        # Final drain of logs | 最后排空日志
        while True:
            try:
                line = log_q.get_nowait()
                if line:
                    yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
            except queue.Empty:
                break

        # Render full message as HTML (backend rendering) | 完整消息渲染为 HTML（后端渲染）
        if full_response:
            try:
                # Convert Markdown to HTML using markdown library | 使用 markdown 库将 Markdown 转为 HTML
                html = markdown.markdown(full_response, extensions=['tables', 'fenced_code'])
                yield f"data: {json.dumps({'type': 'html', 'html': html})}\n\n"
            except Exception as e:
                # Rendering failed, send error but don't interrupt stream | 渲染失败，发送错误但不中断流
                yield f"data: {json.dumps({'type': 'error', 'text': f'Markdown rendering failed | Markdown渲染失败: {str(e)}'})}\n\n"

        # Send stream end signal | 发送流结束信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Store the current Q&A pair into the vector database | 将本轮问答实时存入向量库
        if full_response:
            add_conversation(user_message, full_response)

        # Restore original stdout | 恢复原始标准输出
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
    Get configuration interface | 获取配置接口
    Returns current configuration (excluding sensitive info like API keys) | 返回当前配置（不包含API密钥等敏感信息）

    Returns:
        JSON response of config dict | 配置字典的JSON响应
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
    Update configuration interface | 更新配置接口
    Save configuration and reinitialize agents | 保存配置并重新初始化智能体

    Returns:
        JSON response of operation status or error message | 操作状态或错误信息的JSON响应
    """
    data = request.get_json()
    required = ['api_key', 'base_url', 'model']
    # Check required fields exist | 检查必需字段是否存在
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field} | 缺少字段: {field}'}), 400
    try:
        # Save configuration file | 保存配置文件
        with open("./config.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Reinitialize agents | 重新初始化智能体
        init_agents()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Scheduled task management API | 定时任务管理接口
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks_api():
    """
    Scheduled task management API | 定时任务管理接口
    - GET: return all tasks | GET: 返回所有任务
    - POST: add or delete tasks, distinguished by action parameter | POST: 支持添加或删除任务，通过 action 参数区分
        action=add: add task, requires time and content | action=add: 添加任务，需提供 time 和 content
        action=delete: delete task, requires time | action=delete: 删除任务，需提供 time
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
                return jsonify({'error': 'Missing time or content field | 缺少 time 或 content 字段'}), 400
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
                return jsonify({'error': 'Missing time field | 缺少 time 字段'}), 400
            try:
                if not os.path.exists("./tasks.json"):
                    return jsonify({'error': 'Task file does not exist | 任务文件不存在'}), 404
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                if time_str in tasks:
                    del tasks[time_str]
                    with open("./tasks.json", 'w', encoding='utf-8') as f:
                        json.dump(tasks, f, indent=2, ensure_ascii=False)
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Task does not exist | 任务不存在'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Unknown action | 未知的 action'}), 400

# SSE event stream | SSE 事件流
@app.route('/events')
@login_required
def events():
    """Server-Sent Events endpoint for pushing scheduled task real-time status | Server-Sent Events 端点，用于推送定时任务实时状态"""
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

# Cancel task API | 取消任务接口
@app.route('/cancel_task/<task_id>', methods=['POST'])
@login_required
def cancel_task(task_id):
    """Cancel a running task | 取消正在执行的任务"""
    with active_tasks_lock:
        if task_id in active_tasks:
            active_tasks[task_id].set()
            return jsonify({'status': 'cancelling'})
        else:
            return jsonify({'error': 'Task does not exist or has already ended | 任务不存在或已结束'}), 404

if __name__ == '__main__':
    # Initialize agents | 初始化智能体
    init_agents()
    # Start Cloudflare tunnel in a background thread | 在后台线程中启动 Cloudflare 隧道
    tunnel_thread = threading.Thread(target=start_cloudflare_tunnel, daemon=True)
    tunnel_thread.start()
    # Start web service (127.0.0.1:5000, debug=False to avoid production risks) | 启动Web服务（127.0.0.1:5000，关闭debug模式以避免生产环境风险）
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)