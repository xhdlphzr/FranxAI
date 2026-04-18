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