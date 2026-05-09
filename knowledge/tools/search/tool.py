# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Network Search Tool
Use DuckDuckGo search engine to search internet information
"""

from ddgs import DDGS

def execute(query: str, max_results: int = 5) -> str:
    """
    Search information on the internet

    Args:
        query: Search keyword
        max_results: Maximum number of returned results (default 5)

    Returns:
        Search result list in Markdown format
    """
    try:
        # Create DDGS search engine instance
        with DDGS() as ddgs:
            # Perform text search
            results = list(ddgs.text(query, max_results=max_results))

        # If no search results exist
        if not results:
            return f"No search results found for '{query}'."

        # Format search results
        output = f"🔍 Search results about '{query}':\n\n"
        for i, r in enumerate(results, 1):
            # Get title, link and summary
            title = r.get("title", "No title")
            href = r.get("href", "")
            body = r.get("body", "")[:1000]  # Truncate the first 1000 characters
            output += f"{i}. **{title}**\n"
            output += f"   {body}...\n"
            output += f"   🔍 {href}\n\n"

        return output
    except Exception as e:
        return f"Search failed: {str(e)}"
