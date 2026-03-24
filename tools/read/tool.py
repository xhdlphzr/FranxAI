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
读取文件内容工具
允许AI读取指定文件的内容
"""

from pathlib import Path

def execute(path: str) -> str:
    """
    读取文件内容

    Args:
        path: 文件的完整路径

    Returns:
        文件内容，如果出错则返回错误信息
    """
    try:
        # 解析路径，处理用户目录符号(~)
        p = Path(path).expanduser().resolve()

        # 检查文件是否存在
        if not p.exists():
            return f"错误：文件不存在 - {p}"

        # 检查路径是否为文件
        if not p.is_file():
            return f"错误：路径不是文件 - {p}"

        # 读取文件内容
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except PermissionError:
        return f"错误：没有权限读取文件 - {path}"
    except Exception as e:
        return f"读取文件时发生错误：{str(e)}"
