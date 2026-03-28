<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAI.
FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.
-->

### `read` — 读取文件内容
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