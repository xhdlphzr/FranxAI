<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `write` — 写入、追加或编辑文件内容
- **用途**：当用户请求创建新文件、向现有文件写入内容或修改文件时使用。
- **输入**：
    ```json
    {
        "path": "文件的完整路径",
        "content": "要写入的内容",
        "mode": "overwrite" 或 "append" 或 "edit",
        "start_line": 0,
        "end_line": 0
    }
    ```
    - `path`：**字符串**，必填，文件的完整路径
    - `content`：**字符串**，必填，要写入的内容。在编辑模式下，传入空字符串可删除目标行。
    - `mode`：**字符串**，可选，默认为 "overwrite"。可用值：
        - `"overwrite"`：替换整个文件
        - `"append"`：追加到文件末尾
        - `"edit"`：替换从 `start_line` 到 `end_line` 的行（两端包含，从 1 开始计数）。与 `read` 工具的行号配合使用，实现精确编辑。
    - `start_line`：**整数**，编辑模式下必填。起始行号（从 1 开始，包含该行）。
    - `end_line`：**整数**，编辑模式下必填。结束行号（从 1 开始，包含该行）。
- **输出**：提示操作成功或失败的信息。
- **备注**：
    - 确保写入的内容是用户明确请求的，不要随意修改文件。
    - 如果文件所在的目录不存在，工具会自动创建该目录（需要相应权限）。
    - 在编辑模式下，务必先使用 `read` 获取当前行号，再指定要替换的精确范围。