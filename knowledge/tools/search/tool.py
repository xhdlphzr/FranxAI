# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Network Search Tool | 网络搜索工具
Use DuckDuckGo search engine to search internet information | 使用DuckDuckGo搜索引擎搜索互联网信息
"""

from ddgs import DDGS

def execute(query: str, max_results: int = 5) -> str:
    """
    Search information on the internet | 在互联网上搜索信息

    Args:
        query: Search keyword | 搜索关键词
        max_results: Maximum number of returned results (default 5) | 最大返回结果数（默认5）

    Returns:
        Search result list in Markdown format | 搜索结果列表，格式为Markdown文本
    """
    try:
        # Create DDGS search engine instance | 创建DDGS搜索引擎实例
        with DDGS() as ddgs:
            # Perform text search | 执行文本搜索
            results = list(ddgs.text(query, max_results=max_results))

        # If no search results exist | 如果没有搜索结果
        if not results:
            return f"No search results found for '{query}'. | 未找到关于 '{query}' 的搜索结果。"

        # Format search results | 格式化搜索结果
        output = f"🔍 Search results about '{query}': | 🔍 关于 '{query}' 的搜索结果：\n\n"
        for i, r in enumerate(results, 1):
            # Get title, link and summary | 获取标题、链接和摘要
            title = r.get("title", "No title | 无标题")
            href = r.get("href", "")
            body = r.get("body", "")[:1000]  # Truncate the first 1000 characters | 截取前1000个字符
            output += f"{i}. **{title}**\n"
            output += f"   {body}...\n"
            output += f"   🔍 {href}\n\n"

        return output
    except Exception as e:
        return f"Search failed: {str(e)} | 搜索失败：{str(e)}"