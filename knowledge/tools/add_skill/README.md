<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### add_skill - Add a Skill

Add a skill as a Markdown file and immediately indexes it into the knowledge base for real-time retrieval. Use this when you've completed a complex task and want to remember the solution for future use.

**Parameters:**
- `name` (string, required): Skill name, used as filename. Use lowercase with underscores (e.g., "nginx_setup", "python_venv").
- `content` (string, required): Skill content in Markdown format. Should include: title, scenario, step-by-step solution, and notes.

**When to use:**
- After completing a multi-step task that is worth remembering
- When the user asks you to remember something
- When you discover a reusable solution

**When NOT to use:**
- For simple one-off questions
- For information already covered by existing skills