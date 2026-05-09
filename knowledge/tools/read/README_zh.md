<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `read` — 读取文件内容或项目结构
- **用途**：当用户请求查看文件内容、分析文件中的数据、从文件中获取信息以完成后续任务，或了解项目结构时调用此工具。
- **输入**：
```json
{
    "path": "文件或目录的完整路径"
}
```
    - `path`：**字符串**，必填。路径可以是绝对路径，或基于当前工作目录的相对路径。传入目录路径可扫描项目结构。
- **输出**：
    - **代码文件**（py、js、ts、rs、go、java、c、cpp、cs 等）：返回 `structure` 部分（AST 骨架，包含节点类型、名称和行号范围）和 `content` 部分（带行号的完整文件内容）。使用结构导航，使用行号定位 `write` 工具编辑模式中的精确位置。
    - **非代码文本文件**：返回带行号的文件内容。
    - **文档文件**（PDF、Word、Excel、PowerPoint、CSV）：返回转换后的文本内容。
    - **图片/视频文件**：返回 AI 生成的描述。
    - **目录**：返回项目中所有代码文件的结构地图，显示类、函数、导入及其行号范围。
    - 如果路径不存在或无法读取，将返回错误信息。
- **备注**：此工具只读，不会修改任何文件。请确保路径正确；如有必要，通过其他方式确认文件位置。