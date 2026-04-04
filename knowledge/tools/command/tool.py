# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
Execute System Command Tool | 执行系统命令工具
Allows AI to execute system commands, delete operations are prohibited for security | 允许AI执行系统命令，但禁止执行删除类操作以保证安全
"""

import subprocess

def execute(command: str) -> str:
    """
    Execute system command | 执行系统命令

    Args:
        command: Command string to execute | 要执行的命令字符串

    Returns:
        Command execution result or error message | 命令执行结果或错误信息
    """
    # Convert command to lowercase for security check | 将命令转换为小写进行安全检测
    cmd_lower = command.lower()

    # Define dangerous command pattern list | 定义危险命令模式列表
    dangerous_patterns = [
        "rm ", "del ", "rmdir ", "rd ", "erase ", "shred ", "unlink ",
        "remove-item", "ri ", "rmdir /s", "rd /s", "remove-item -recurse",
        "rm -r", "rm -f", "rm -rf",
        " && rmdir", " && del", " | rmdir", " | del"
    ]

    # Check if it contains dangerous command patterns | 检测是否包含危险命令模式
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return ("❌ Error: Deletion commands are prohibited. FranxAI security rules do not allow direct deletion of files or folders. | ❌ 错误：禁止执行删除类命令。FranxAI 的安全规则不允许直接删除文件或文件夹。"
                    "If you need to clean up files, please tell me to use 'move' operation, I will help you move files to 'C:\\ToBeDeleted' directory. | 如果你需要清理文件，请告诉我用 'move' 操作，我会帮你把文件移动到 'C:\\待删除' 目录。")

    try:
        # Execute command, capture output and errors | 执行命令，捕获输出和错误
        result = subprocess.run(command, shell=True, capture_output=True, timeout=30)
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        output = stdout + stderr

        # If command returns non-zero exit code, add error message to output | 如果命令返回非零退出码，在输出中添加错误信息
        if result.returncode != 0:
            output = f"Command returned non-zero exit code {result.returncode}\n{output} | 命令返回非零退出码 {result.returncode}\n{output}"
        # If no output, return success message | 如果没有输出，返回成功消息
        return output.strip() or "Command executed successfully (no output) | 命令执行成功（无输出）"
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out | 错误：命令执行超时"
    except Exception as e:
        return f"Execution failed: {e} | 执行失败：{e}"