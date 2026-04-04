# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
File Write Tool | 写入文件工具
Allows the AI to write or append content to a specified file | 允许AI写入或追加内容到指定文件
"""

from pathlib import Path

def execute(path: str, content: str, mode="overwrite") -> str:
    """
    Write or append content to a file | 写入或追加内容到文件

    Args:
        path: Full path of the file | 文件的完整路径
        content: Content to be written | 要写入的内容
        mode: Write mode, "overwrite" (overwrite) or "append" (append), default is "overwrite" | 写入模式，"overwrite"（覆盖）或 "append"（追加），默认为 "overwrite"

    Returns:
        Operation result information | 操作结果信息
    """
    try:
        # Resolve the path and handle user directory symbol (~) | 解析路径，处理用户目录符号(~)
        p = Path(path).expanduser().resolve()

        # Ensure the parent directory exists | 确保父目录存在
        p.parent.mkdir(parents=True, exist_ok=True)

        # Select file opening mode based on the parameter | 根据模式选择文件打开方式
        flag = 'a' if mode == 'append' else 'w'

        # Write content to the file | 写入内容
        with open(p, flag, encoding='utf-8') as f:
            f.write(content)

        # Return success message | 返回成功信息
        return f"Successfully {'appended to' if mode=='append' else 'wrote to'} file: {p} | 成功{'追加' if mode=='append' else '写入'}文件：{p}"
    except Exception as e:
        return f"Write failed: {e} | 写入失败：{e}"