<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `read` - Read File Content or Project Structure
- **Purpose**: Call this tool when the user requests to view the content of a file, analyze data within a file, obtain information from a file to complete subsequent tasks, or understand the structure of a project.
- **Input**:
```json
{
    "path": "Full path of the file or directory"
}
```
    - `path`: **string**, required. The path can be an absolute path, or a relative path based on the current working directory. Pass a directory path to scan the project structure.
- **Output**:
    - **Code files** (py, js, ts, rs, go, java, c, cpp, cs, etc.): Returns a `structure` section (AST skeleton with node types, names, and line ranges) followed by a `content` section (full file with line numbers). Use the structure to navigate, and the line numbers to locate exact positions for the `write` tool's edit mode.
    - **Non-code text files**: Returns file content with line numbers.
    - **Document files** (PDF, Word, Excel, PowerPoint, CSV): Returns converted text content.
    - **Image/Video files**: Returns an AI-generated description.
    - **Directory**: Returns a structure map of all code files in the project, showing classes, functions, imports, and their line ranges.
    - An error message will be returned if the path does not exist or cannot be read.
- **Notes**: This tool is read-only and will not modify any files. Ensure the path is correct; confirm the file location via other methods if necessary.