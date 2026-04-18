<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `read` - Read File Content
- **Purpose**: Call this tool when the user requests to view the content of a file, analyze data within a file, or when you need to obtain information from a file to complete subsequent tasks.
- **Input**:
```json
{
    "path": "Full path of the file"
}
```
    - `path`: **string**, required. The path can be an absolute path, or a relative path based on the current working directory.
- **Output**: File content (text format) or image/video description (if the file is an image or video file). An error message will be returned if the file does not exist or cannot be read.
- **Notes**: This tool is read-only and will not modify the file. Ensure the path is correct; confirm the file location via other methods if necessary.