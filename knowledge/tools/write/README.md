<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `write` — Write or append file content | 写入或追加文件内容
- **Purpose**: Used when the user requests creating new files, writing content to existing files, or modifying files.
- **Input**:
  ```json
  {
    "path": "Full path of the file",
    "content": "Content to write",
    "mode": "overwrite" or "append"  // Default: "overwrite"
  }
  ```
  - `path`: **string**, required, full path of the file
  - `content`: **string**, required, content to be written
  - `mode`: **string**, optional, default is "overwrite". Available values: "overwrite" for replacement, "append" for adding content
- **Output**: Prompt message indicating whether the operation succeeded or failed.
- **Notes**:
  - Ensure the written content is explicitly requested by the user; do not modify files arbitrarily.
  - If the directory where the file is located does not exist, the tool will automatically create the directory (permissions required).
- **用途**：当用户要求创建新文件、向现有文件中写入内容、修改文件时使用。
- **输入**：
  ```json
  {
    "path": "文件的完整路径",
    "content": "要写入的内容",
    "mode": "overwrite" 或 "append"  // 默认 "overwrite"
  }
  ```
  - `path`：**string**，必填，文件的完整路径
  - `content`：**string**，必填，要写入的内容
  - `mode`：**string**，可选，默认为"overwrite"，可选值："overwrite"覆盖、"append"追加
- **输出**：操作成功或失败的提示信息。
- **注意事项**：
  - 请确保写入的内容是用户明确要求的，不要随意修改文件。
  - 如果文件所在目录不存在，工具会自动创建目录（需要权限）。