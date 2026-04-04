# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
Flask Web应用模块
提供Web界面和API接口，支持实时聊天、配置管理和定时任务执行
"""

import os
import json
import queue
import threading
import time
import sys
import io
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from agent import FranxAI
import markdown

sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge import search, add_conversation

# 创建Flask应用实例
app = Flask(__name__)
app.secret_key = 'FranxAI'

# 启动时的时间戳，用于会话验证
STARTUP_ID = str(int(time.time()))

def load_config():
    """
    加载配置文件

    Returns:
        配置字典
    """
    with open("./config.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """
    保存配置文件

    Args:
        config: 要保存的配置字典
    """
    with open("./config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# 全局变量：聊天智能体和任务智能体
chat_agent = None
chat_agent_lock = threading.Lock()  # 用于线程安全的锁
tasks_agent = None

# 定时任务 SSE 广播器
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

# 存储正在执行的任务取消事件
active_tasks = {}
active_tasks_lock = threading.Lock()

def init_agents():
    global chat_agent, tasks_agent, last_config_mtime
    config = load_config()
    last_config_mtime = os.path.getmtime("./config.json")
    
    temperature = config.get("temperature", 0.8)
    thinking = config.get("thinking", False)
    max_iterations = config.get("max_iterations", 100)
    threshold = config.get("threshold", 20)
    knowledge_k = config.get("knowledge_k", 1)
    
    settings = config.get("settings", "你是一个有用的AI助手。")
    
    # 聊天智能体
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
    
    # 任务智能体
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

# 定时任务执行函数（支持取消和流式推送）
def execute_task(task_id, content, cancel_event):
    """执行单个定时任务，并将过程实时推送到 SSE"""
    # 发送开始事件
    broadcaster.broadcast('task_start', {
        'task_id': task_id,
        'content': content,
        'message': f"⏰ 执行定时任务: {content}"
    })

    try:
        result_parts = []
        # 迭代生成器，实时推送每个 chunk
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
        # 发送完成事件
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
    定时任务执行器
    每隔10秒检查一次tasks.json，执行当前时间对应的任务
    文件格式：{"HH:MM": "命令内容"}
    """
    # 初始化执行记录集合和上次执行日期
    if not hasattr(run_tasks, "_executed"):
        run_tasks._executed = set()
    if not hasattr(run_tasks, "_last_date"):
        run_tasks._last_date = None

    while True:
        # 检查任务文件是否存在
        if os.path.exists("./tasks.json"):
            try:
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            except:
                pass
            else:
                # 获取当前时间
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                today = now.strftime("%Y-%m-%d")

                # 如果是新的一天，重置执行记录
                if today != run_tasks._last_date:
                    run_tasks._executed.clear()
                    run_tasks._last_date = today

                # 遍历所有任务（键为时间，值为命令）
                for time_str, content in tasks.items():
                    if time_str == current_time and time_str not in run_tasks._executed:
                        # 生成唯一任务ID
                        task_id = str(uuid.uuid4())
                        cancel_event = threading.Event()
                        with active_tasks_lock:
                            active_tasks[task_id] = cancel_event
                        # 启动执行线程
                        thread = threading.Thread(target=execute_task, args=(task_id, content, cancel_event))
                        thread.daemon = True
                        thread.start()
                        run_tasks._executed.add(time_str)
        # 睡眠10秒后再次检查
        time.sleep(10)

# 启动定时任务线程
run_tasks_thread = threading.Thread(target=run_tasks, daemon=True)
run_tasks_thread.start()

@app.route('/')
def index():
    """
    根路径路由
    返回Web聊天界面模板

    Returns:
        渲染后的HTML页面
    """
    return render_template('index.html')

@app.route('/session', methods=['GET'])
def get_session():
    """
    获取会话ID
    用于前端验证会话是否有效

    Returns:
        包含startup_id的JSON响应
    """
    return jsonify({'startup_id': STARTUP_ID})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', STARTUP_ID)   # 前端可传递会话ID，默认使用 STARTUP_ID
    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400

    def generate():
        # 保存原始标准输出
        old_stdout = sys.stdout
        # 用于兼容原逻辑的缓冲区（实际不再发送，仅用于写入）
        sio = io.StringIO()
        # 引入队列用于实时日志
        log_q = queue.Queue()

        # 自定义输出流：每个 print 同时写入原缓冲区和实时队列
        class QueueStream(io.TextIOBase):
            def write(self, s):
                if s:
                    log_q.put(s)
                return sio.write(s)

        # 重定向标准输出到自定义流
        sys.stdout = QueueStream()

        # 累积完整回复
        full_response = ""

        # ---------- 检索知识并发送到前端 ----------
        try:
            # 从 agent 获取 knowledge_k，如果不存在则默认 1
            k = getattr(chat_agent, 'knowledge_k', 1)
            relevant = search(user_message, k=k)
            for item in relevant:
                # 每条知识单独发送一个 knowledge 事件
                yield f"data: {json.dumps({'type': 'knowledge', 'text': item})}\n\n"
        except Exception as e:
            # 检索失败不影响主流程，仅打印日志
            print(f"知识检索失败: {e}")

        try:
            with chat_agent_lock:
                # 流式输出 AI 回复（原有逻辑）
                for chunk in chat_agent.input(user_message):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"
                    # 每次输出回复后，立即将队列中的日志实时发送
                    while True:
                        try:
                            line = log_q.get_nowait()
                            if line:
                                yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
                        except queue.Empty:
                            break
                # 记忆压缩（原有逻辑）
                chat_agent.memory()
        except Exception as e:
            # 错误处理
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
        finally:
            # 恢复原始标准输出
            sys.stdout = old_stdout

        # 完整消息渲染为 HTML（后端渲染）
        if full_response:
            try:
                # 使用 markdown 库将 Markdown 转为 HTML
                html = markdown.markdown(full_response)
                yield f"data: {json.dumps({'type': 'html', 'html': html})}\n\n"
            except Exception as e:
                # 渲染失败，发送错误但不中断流
                yield f"data: {json.dumps({'type': 'error', 'text': f'Markdown渲染失败: {str(e)}'})}\n\n"

        # 发送流结束信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # 将本轮问答实时存入向量库
        if full_response:
            add_conversation(user_message, full_response)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

@app.route('/config', methods=['GET'])
def get_config():
    """
    获取配置接口
    返回当前配置（不包含API密钥等敏感信息）

    Returns:
        配置字典的JSON响应
    """
    try:
        with open("./config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config', methods=['POST'])
def update_config():
    """
    更新配置接口
    保存配置并重新初始化智能体

    Returns:
        操作状态或错误信息的JSON响应
    """
    data = request.get_json()
    required = ['api_key', 'base_url', 'model']
    # 检查必需字段是否存在
    for field in required:
        if field not in data:
            return jsonify({'error': f'缺少字段: {field}'}), 400
    try:
        # 保存配置文件
        with open("./config.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # 重新初始化智能体
        init_agents()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 定时任务管理接口
@app.route('/tasks', methods=['GET', 'POST'])
def tasks_api():
    """
    定时任务管理接口
    - GET: 返回所有任务
    - POST: 支持添加或删除任务，通过 action 参数区分
        action=add: 添加任务，需提供 time 和 content
        action=delete: 删除任务，需提供 time
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
                return jsonify({'error': '缺少 time 或 content 字段'}), 400
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
                return jsonify({'error': '缺少 time 字段'}), 400
            try:
                if not os.path.exists("./tasks.json"):
                    return jsonify({'error': '任务文件不存在'}), 404
                with open("./tasks.json", 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                if time_str in tasks:
                    del tasks[time_str]
                    with open("./tasks.json", 'w', encoding='utf-8') as f:
                        json.dump(tasks, f, indent=2, ensure_ascii=False)
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': '任务不存在'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': '未知的 action'}), 400

# SSE 事件流
@app.route('/events')
def events():
    """Server-Sent Events 端点，用于推送定时任务实时状态"""
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

# 取消任务接口
@app.route('/cancel_task/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消正在执行的任务"""
    with active_tasks_lock:
        if task_id in active_tasks:
            active_tasks[task_id].set()
            return jsonify({'status': 'cancelling'})
        else:
            return jsonify({'error': '任务不存在或已结束'}), 404

if __name__ == '__main__':
    # 初始化智能体
    init_agents()
    # 启动Web服务（127.0.0.1:5000，关闭debug模式以避免生产环境风险）
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)