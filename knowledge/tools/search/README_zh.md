<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### search - 网络搜索
- **用途**：搜索互联网信息，获取实时数据、新闻、百科内容等。
- **输入**：
    - `query`：**字符串**，必填，搜索关键词
    - `max_results`：**整数**，可选，返回结果数量（默认：5）
- **输出**：格式化的搜索结果列表，每项包含标题、摘要和链接。
- **备注**：
    - 完全免费，无需 API Key。
    - 实时搜索结果，与浏览器中使用的 DuckDuckGo 一致。
    - 请合理使用，避免在短时间内发送大量请求。