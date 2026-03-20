import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
TASKS_FILE = PROJECT_ROOT / "tasks.json"

def execute(content: str, time: str) -> str:
    tasks = {}
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            if not isinstance(tasks, dict):
                tasks = {}
        except Exception as e:
            return f"读取任务文件失败: {e}"

    max_id = 0
    for key in tasks.keys():
        try:
            if int(key) > max_id:
                max_id = int(key)
        except:
            continue
    new_id = max_id + 1

    tasks[str(new_id)] = [content, time]

    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        return f"任务已添加！ID: {new_id}, 内容: {content}, 时间: {time}"
    except Exception as e:
        return f"写入任务文件失败: {e}"