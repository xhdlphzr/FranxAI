<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `read` - Read File Content | 读取文件内容
- **Purpose**: Call this tool when the user requests to view the content of a file, analyze data within a file, or when you need to obtain information from a file to complete subsequent tasks.
- **Input**:
```json
{
  "path": "Full path of the file"
}
```
  - `path`: **string**, required. The path can be an absolute path, or a relative path based on the current working directory.
- **Output**: File content (text format). An error message will be returned if the file does not exist or cannot be read.
- **Notes**: This tool is read-only and will not modify the file. Ensure the path is correct; confirm the file location via other methods if necessary.
- **用途**：当用户要求查看某个文件的内容、分析文件中的数据、或者你需要从文件中获取信息以完成后续任务时，请调用此工具。
- **输入**：
  ```json
  {
    "path": "文件的完整路径"
  }
  ```
  - `path`：**string**，必填。路径可以是绝对路径，也可以是基于当前工作目录的相对路径。
- **输出**：文件的内容（文本格式）。如果文件不存在或无法读取，会返回错误信息。
- **注意事项**：此工具是只读的，不会修改文件。确保路径正确，必要时可先用其他方式确认文件位置。