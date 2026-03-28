<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAI.
FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.
-->

### search — 网络搜索
- **用途**：搜索互联网信息，获取实时数据、新闻、百科内容等。
- **输入**：
  - `query`：**string**，必填，搜索关键词
  - `max_results`：**integer**，可选，返回条数（默认 5）
- **输出**：格式化后的搜索结果列表，每条包含标题、摘要、链接。
- **注意事项**：
  - 完全免费，无需 API Key。
  - 搜索结果是实时的，与浏览器中使用 DuckDuckGo 一致。
  - 请合理使用，避免短时间内大量请求。