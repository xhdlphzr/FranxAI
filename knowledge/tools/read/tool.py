# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
File Content Reading Tool | 读取文件内容工具
Allows the AI to read the content of a specified file | 允许AI读取指定文件的内容
"""

from pathlib import Path

def execute(path: str) -> str:
    """
    Read file content | 读取文件内容

    Args:
        path: Full path of the file | 文件的完整路径

    Returns:
        File content, returns error message if an error occurs | 文件内容，如果出错则返回错误信息
    """
    try:
        # Resolve the path and handle user directory symbol (~) | 解析路径，处理用户目录符号(~)
        p = Path(path).expanduser().resolve()

        # Check if the file exists | 检查文件是否存在
        if not p.exists():
            return f"Error: File does not exist - {p} | 错误：文件不存在 - {p}"

        # Check if the path is a file | 检查路径是否为文件
        if not p.is_file():
            return f"Error: Path is not a file - {p} | 错误：路径不是文件 - {p}"

        # Read file content | 读取文件内容
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except PermissionError:
        return f"Error: No permission to read the file - {path} | 错误：没有权限读取文件 - {path}"
    except Exception as e:
        return f"An error occurred while reading the file: {str(e)} | 读取文件时发生错误：{str(e)}"