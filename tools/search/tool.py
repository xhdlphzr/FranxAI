from ddgs import DDGS

def execute(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return f"未找到关于 '{query}' 的搜索结果。"
        
        output = f"🔍 关于 '{query}' 的搜索结果：\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            href = r.get("href", "")
            body = r.get("body", "")[:1000]
            output += f"{i}. **{title}**\n"
            output += f"   {body}...\n"
            output += f"   🔗 {href}\n\n"
        
        return output
    except Exception as e:
        return f"搜索失败：{str(e)}"