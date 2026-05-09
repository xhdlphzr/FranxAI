<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### add_skill — 添加技能

将技能添加为 Markdown 文件，并立即索引到知识库中实现实时检索。当你完成了一项复杂任务并希望记住该解决方案以备将来使用时，请使用此工具。

**参数：**
- `name`（字符串，必填）：技能名称，用作文件名。使用小写字母和下划线（例如 "nginx_setup"、"python_venv"）。
- `content`（字符串，必填）：Markdown 格式的技能内容。应包含：标题、适用场景、分步解决方案和注意事项。

**何时使用：**
- 完成值得记住的多步骤任务后
- 当用户要求你记住某些内容时
- 当你发现可复用的解决方案时

**何时不使用：**
- 简单的一次性问题
- 已被现有技能覆盖的信息