<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
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
    - **edit 模式的关键规则 — 行号锁定 (只认读取，严禁推测)**：
        - **所有 `start_line` 和 `end_line` 的值必须且只能来源于最近一次的 `read` 操作。** 严禁根据编辑内容去预测、计算或推断行号。
        - **只认原始文件：** 当需要删除或替换行时，必须使用文件在被编辑前的原始行号。例如：如果 `read` 显示了第 50-60 行，现在要用一个 6 行的代码块替换掉原来的 54-57 行，那么**必须**填 `start_line=54, end_line=57`。填成 `54-59`（编辑后推算的行号）是极其严重的违规行为。
        - **禁止漂移修正：** 绝对不要为了“对齐”而自行调整行号，去预估编辑后各行会移动到哪里。那是系统内部处理的事，你的职责仅仅是提供精准的“当前坐标”。
        - **执行前复检：** 在调用 `edit` 模式之前，必须在你的执行计划中明确声明：“我将替换的是最近一次 `read` 操作中显示的第 X 行到第 Y 行。”