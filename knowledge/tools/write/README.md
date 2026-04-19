<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `write` — Write, append, or edit file content
- **Purpose**: Used when the user requests creating new files, writing content to existing files, or modifying files.
- **Input**:
    ```json
    {
        "path": "Full path of the file",
        "content": "Content to write",
        "mode": "overwrite" or "append" or "edit",
        "start_line": 0,
        "end_line": 0
    }
    ```
    - `path`: **string**, required, full path of the file
    - `content`: **string**, required, content to be written. In edit mode, pass empty string to delete the target lines.
    - `mode`: **string**, optional, default is "overwrite". Available values:
        - `"overwrite"`: Replace entire file
        - `"append"`: Append to end of file
        - `"edit"`: Replace lines from `start_line` to `end_line` (both inclusive, 1-based). Use with `read` tool's line numbers for precise editing.
    - `start_line`: **integer**, required in edit mode. Start line number (1-based, inclusive).
    - `end_line`: **integer**, required in edit mode. End line number (1-based, inclusive).
- **Output**: Prompt message indicating whether the operation succeeded or failed.
- **Notes**:
    - Ensure the written content is explicitly requested by the user; do not modify files arbitrarily.
    - If the directory where the file is located does not exist, the tool will automatically create the directory (permissions required).
    - In edit mode, always use `read` first to get the current line numbers, then specify the exact range to replace.