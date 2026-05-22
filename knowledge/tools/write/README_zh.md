<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `write` — 提议文件内容更改（提案-审查-覆写模式）
- **用途**：当 AI 想要创建新文件、向现有文件写入内容或修改文件时使用。write 工具**不再执行任何磁盘操作**，而是返回 AI 建议的完整文件内容字符串。前端在代码审查面板中显示该内容，用户可查看差异、编辑代码并批准更改。
- **输入**：
    ```json
    {
        "path": "文件的完整路径",
        "content": "完整文件内容",
        "mode": "overwrite" 或 "append" 或 "edit",
        "start_line": 0,
        "end_line": 0
    }
    ```
    - `path`：**字符串**，必填，目标文件的完整路径。
    - `content`：**字符串**，必填，AI 建议的修改后的完整文件内容。前端会将该内容与当前磁盘上的文件进行 diff。
    - `mode`：**字符串**，可选，默认为 "overwrite"。可用值：
        - `"overwrite"`：替换整个文件。
        - `"append"`：在 `start_line` 指定的行**之后**插入内容（当 `start_line > 0` 时），否则追加到文件末尾。`end_line` 被忽略。
        - `"edit"`：替换从 `start_line` 到 `end_line` 的行（两端包含，从 1 开始计数）。与 `read` 工具的行号配合使用，实现精确编辑。
    - `start_line`：**整数**，编辑模式和 append 模式下（仅当需要在特定行后插入时）必填。起始行号（从 1 开始，包含该行）。若 append 模式下 `start_line <= 0`，内容追加到文件末尾。
    - `end_line`：**整数**，编辑模式下必填。结束行号（从 1 开始，包含该行）。
- **输出**：AI 建议的完整文件内容，以纯字符串形式返回（不是字典）。
- **工作流程**：
    1. AI 调用 `write` 工具并提供建议的文件内容。
    2. 后端将内容字符串返回给前端，不触碰磁盘。
    3. 前端打开代码审查面板，显示原始文件与 AI 提议之间的差异。
    4. 用户可切换到编辑模式修改代码，然后批准更改。
    5. 批准后，前端写入文件并将最终内容回传给 AI，以保持同步。
- **备注**：
    - 该工具不执行任何文件操作。所有磁盘写入均由前端在用户批准后执行。
    - **带 `start_line` 的 Append 模式**：  
      例如，文件包含行 `1: a`、`2: b`。调用 `write` 并设置 `mode="append"`、`start_line=1`、`content="X"`，结果：  
      ```
      a
      X
      b
      ```
      如果 `start_line >= 总行数`，内容插入到最后一行之后（等效于追加）。
    - **Edit 模式**：务必先使用 `read` 获取当前行号，再指定要替换的精确范围。
    - **edit 模式的关键规则 — 行号锁定（只认读取，严禁推测）**：
        - **所有 `start_line` 和 `end_line` 的值必须且只能来源于最近一次的 `read` 操作。** 严禁根据编辑内容去预测、计算或推断行号。
        - **只认原始文件：** 当需要删除或替换行时，必须使用文件在被编辑前的原始行号。例如：如果 `read` 显示了第 50-60 行，现在要用一个 6 行的代码块替换掉原来的 54-57 行，那么**必须**填 `start_line=54, end_line=57`。填成 `54-59`（编辑后推算的行号）是极其严重的违规行为。
        - **禁止漂移修正：** 绝对不要为了“对齐”而自行调整行号，去预估编辑后各行会移动到哪里。那是系统内部处理的事，你的职责仅仅是提供精准的“当前坐标”。
        - **执行前复检：** 在调用 `edit` 模式之前，必须在你的执行计划中明确声明：“我将替换的是最近一次 `read` 操作中显示的第 X 行到第 Y 行。”