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
网络搜索工具
使用DuckDuckGo搜索引擎搜索互联网信息
"""

from ddgs import DDGS

def execute(query: str, max_results: int = 5) -> str:
    """
    在互联网上搜索信息

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数（默认5）

    Returns:
        搜索结果列表，格式为Markdown文本
    """
    try:
        # 创建DDGS搜索引擎实例
        with DDGS() as ddgs:
            # 执行文本搜索
            results = list(ddgs.text(query, max_results=max_results))

        # 如果没有搜索结果
        if not results:
            return f"未找到关于 '{query}' 的搜索结果。"

        # 格式化搜索结果
        output = f"🔍 关于 '{query}' 的搜索结果：\n\n"
        for i, r in enumerate(results, 1):
            # 获取标题、链接和摘要
            title = r.get("title", "无标题")
            href = r.get("href", "")
            body = r.get("body", "")[:1000]  # 截取前1000个字符
            output += f"{i}. **{title}**\n"
            output += f"   {body}...\n"
            output += f"   🔗 {href}\n\n"

        return output
    except Exception as e:
        return f"搜索失败：{str(e)}"
