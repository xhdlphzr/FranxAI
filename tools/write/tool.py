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
写入文件工具
允许AI写入或追加内容到指定文件
"""

from pathlib import Path

def execute(path: str, content: str, mode="overwrite") -> str:
    """
    写入或追加内容到文件

    Args:
        path: 文件的完整路径
        content: 要写入的内容
        mode: 写入模式，"overwrite"（覆盖）或 "append"（追加），默认为 "overwrite"

    Returns:
        操作结果信息
    """
    try:
        # 解析路径，处理用户目录符号(~)
        p = Path(path).expanduser().resolve()

        # 确保父目录存在
        p.parent.mkdir(parents=True, exist_ok=True)

        # 根据模式选择文件打开方式
        flag = 'a' if mode == 'append' else 'w'

        # 写入内容
        with open(p, flag, encoding='utf-8') as f:
            f.write(content)

        # 返回成功信息
        return f"成功{'追加' if mode=='append' else '写入'}文件：{p}"
    except Exception as e:
        return f"写入失败：{e}"
