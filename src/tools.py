from datetime import datetime
from pathlib import Path
import subprocess

def get_time() -> str:
    now = datetime.now()

    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]

    return now.strftime(f"%Y-%m-%d {weekday} %H:%M:%S")

def read_file(path: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"错误：文件不存在 - {p}"
        if not p.is_file():
            return f"错误：路径不是文件 - {p}"
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except PermissionError:
        return f"错误：没有权限读取文件 - {path}"
    except Exception as e:
        return f"读取文件时发生错误：{str(e)}"
    
def write_file(path: str, content: str, mode="overwrite") -> str:
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        flag = 'a' if mode == 'append' else 'w'
        with open(p, flag, encoding='utf-8') as f:
            f.write(content)
        return f"成功{'追加' if mode=='append' else '写入'}文件：{p}"
    except Exception as e:
        return f"写入失败：{e}"
    
def execute_command(command):
    dangerous = ["rm", "del", "rmdir", "rd", "erase", "shred", "unlink"]
    first = command.strip().split()[0].lower()
    if first in dangerous:
        return ("错误：禁止直接执行删除命令。如需删除文件，请使用移动操作 "
                "（如：mv 文件 ~/.Trash/ 或 move 文件 C:\\待删除\\）")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return output.strip() or "命令执行成功（无输出）"
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时"
    except Exception as e:
        return f"执行失败：{e}"