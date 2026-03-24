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
添加定时任务工具
允许AI在指定时间添加一个定时任务，任务会自动执行
"""

import json
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
# 定义任务文件路径
TASKS_FILE = PROJECT_ROOT / "tasks.json"

def execute(content: str, time: str) -> str:
    """
    添加一个定时任务

    Args:
        content: 任务描述内容
        time: 执行时间，格式为 "HH:MM"（24小时制）

    Returns:
        操作结果信息
    """
    tasks = {}
    # 如果任务文件已存在，尝试加载它
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            # 确保tasks是字典类型
            if not isinstance(tasks, dict):
                tasks = {}
        except Exception as e:
            return f"读取任务文件失败: {e}"

    # 查找当前最大的ID
    max_id = 0
    for key in tasks.keys():
        try:
            if int(key) > max_id:
                max_id = int(key)
        except:
            continue
    # 新任务的ID为当前最大ID + 1
    new_id = max_id + 1

    # 将新任务添加到字典中
    tasks[str(new_id)] = [content, time]

    try:
        # 将任务写入文件
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        return f"任务已添加！ID: {new_id}, 内容: {content}, 时间: {time}"
    except Exception as e:
        return f"写入任务文件失败: {e}"
