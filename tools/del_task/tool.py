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
删除定时任务工具
允许AI删除指定的定时任务，并自动重新对齐后续任务的ID
"""

import json
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
# 定义任务文件路径
TASKS_FILE = PROJECT_ROOT / "tasks.json"

def execute(id: int) -> str:
    """
    删除指定ID的定时任务

    Args:
        id: 要删除的任务ID（整数）

    Returns:
        操作结果信息
    """
    # 检查任务文件是否存在
    if not TASKS_FILE.exists():
        return f"任务文件不存在，无法删除ID {id}。"

    try:
        # 读取任务文件
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception as e:
        return f"读取任务文件失败: {e}"

    # 检查任务文件格式
    if not isinstance(tasks, dict):
        return "任务文件格式错误。"

    # 将ID转换为字符串进行查找
    str_id = str(id)
    if str_id not in tasks:
        return f"未找到ID为 {id} 的任务。"

    # 删除指定ID的任务
    del tasks[str_id]

    # 如果任务列表为空，清空文件
    if not tasks:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
        return f"已删除ID {id} 的任务，现在无剩余任务。"

    # 重新对齐任务ID（删除后，所有大于该ID的任务ID减1）
    sorted_items = sorted(tasks.items(), key=lambda x: int(x[0]))

    new_tasks = {}
    new_id = 1
    for _, value in sorted_items:
        new_tasks[str(new_id)] = value
        new_id += 1

    try:
        # 将重新对齐后的任务写入文件
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"写入任务文件失败: {e}"

    return f"已删除ID {id} 的任务，并重新对齐任务ID（原ID大于{id}的任务ID均已减1）。"
