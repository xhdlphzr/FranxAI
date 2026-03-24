# Copyright (C) 2026 xhdlphzr
#
# This file is part of EasyMate.
#
# EasyMate is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
#
# EasyMate is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with EasyMate.  If not, see <https://www.gnu.org/licenses/>.

"""
Flask Web应用模块
提供Web界面和API接口，支持实时聊天、配置管理和定时任务执行
"""

import os
import json
import queue
import threading
import time
import atexit
import sys
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from agent import EasyMate

# 创建Flask应用实例
app = Flask(__name__)
app.secret_key = 'EasyMate'

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

def init_agents():
    global chat_agent, tasks_agent, last_config_mtime
    config = load_config()
    last_config_mtime = os.path.getmtime("./config.json")
    
    temperature = config.get("temperature", 0.8)
    thinking = config.get("thinking", False)
    max_iterations = config.get("max_iterations", 100)
    threshold = config.get("threshold", 20)
    
    pre_memory = ""
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            pre_memory = f.read()
    except:
        pass
    
    settings = config.get("settings", "你是一个有用的AI助手。")
    full_settings = f"{settings}\n\n{pre_memory}" if pre_memory else settings
    
    # 聊天智能体
    chat_agent = EasyMate(
        key=config["api_key"],
        url=config["base_url"],
        model=config["model"],
        settings=full_settings,
        max_iterations=max_iterations,
        temperature=temperature,
        thinking=thinking,
        threshold=threshold
    )
    
    # 任务智能体
    tasks_agent = EasyMate(
        key=config["api_key"],
        url=config["base_url"],
        model=config["model"],
        settings=full_settings,
        max_iterations=max_iterations,
        temperature=temperature,
        thinking=thinking,
        threshold=threshold
    )

def save_memory_on_exit():
    """
    退出时保存记忆到文件
    使用atexit注册，程序退出时自动调用
    """
    global chat_agent
    if chat_agent and len(chat_agent.messages) > 1:
        try:
            # 生成摘要（不使用生成器，直接获取完整字符串）
            summary = ''.join(chat_agent.summarize_msg(len(chat_agent.messages)))
            if summary:
                with open("memory.txt", "w", encoding="utf-8") as f:
                    f.write(summary)
                print("已保存记忆到 memory.txt")
            else:
                print("退出时无法生成摘要（摘要为空）")
        except KeyboardInterrupt:
            # 用户手动中断，不保存记忆
            print("退出时未保存记忆（用户中断）")
        except Exception as e:
            print(f"保存记忆失败: {e}")

# 注册退出时保存记忆的回调函数
atexit.register(save_memory_on_exit)

def run_tasks():
    """
    定时任务执行器
    每隔10秒检查一次tasks.json，执行当前时间对应的任务
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

                # 遍历所有任务，执行当前时间的任务
                for task_id, (content, time_str) in tasks.items():
                    if time_str == current_time and task_id not in run_tasks._executed:
                        print(f"执行任务 {task_id}: {content}")
                        try:
                            # 使用任务智能体执行任务
                            tasks_agent.input(content)
                        except Exception as e:
                            print(f"任务执行失败: {e}")
                        run_tasks._executed.add(task_id)
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

        try:
            with chat_agent_lock:
                # 流式输出 AI 回复（原有逻辑）
                for chunk in chat_agent.input(user_message):
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

        # 发送流结束信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

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

if __name__ == '__main__':
    # 初始化智能体
    init_agents()
    # 启动Web服务（127.0.0.1:5000，关闭debug模式以避免生产环境风险）
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)