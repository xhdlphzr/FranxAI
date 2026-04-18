<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### search - Web Search
- **Purpose**: Search internet information to obtain real-time data, news, encyclopedia content and more.
- **Input**:
    - `query`: **string**, required, search keyword
    - `max_results`: **integer**, optional, number of returned results (default: 5)
- **Output**: Formatted list of search results; each item contains a title, summary and link.
- **Notes**:
    - Completely free, no API Key required.
    - Real-time search results, consistent with DuckDuckGo used in browsers.
    - Please use reasonably, avoid sending a large number of requests in a short period of time.
