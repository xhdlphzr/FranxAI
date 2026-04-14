# Contribution Guide
Thank you for your interest in FranxAgent! We welcome all forms of contributions, including new features, tool plugins, **skills**, documentation improvements, bug reports, and more. To ensure smooth collaboration, please follow the processes and standards below.

---

## 📦 Tool Contribution (Most Common)
If you wish to add a new tool to FranxAgent (such as `weather`, `calc`, etc.), please follow these steps:

### 1. Fork the Repository
- Visit the [FranxAgent Repository](https://github.com/xhdlphzr/FranxAgent) and click **Fork** in the top-right corner to copy the repository to your GitHub account.

### 2. Clone Your Fork Locally
```bash
git clone https://github.com/xhdlphzr/FranxAgent.git
cd FranxAgent
```

### 3. Create a New Branch
```bash
git checkout -b add-tool-name
```
Example: `add-weather`.

### 4. Add Tool Files
Create a folder named after the tool on the `tools` branch (e.g., `weather/`).
This folder **must** contain the two files below:

#### a. `tool.py`
- Must include a function named `execute` that accepts keyword arguments and returns a string result.
- Example:
  ```python
  def execute(city: str) -> str:
      # Implement weather query logic
      return f"The weather in {city} is sunny, 25°C"
  ```

#### b. `README.md`
- Briefly describe the tool’s purpose, inputs, outputs, and notes in a clear format (follow the style of existing tools).
- For examples, see `knowledge/tools/time/README.md` on the `main` branch.

### 5. Local Testing
Make sure your tool imports and works properly (you may temporarily modify `src/main.py` for testing).
Run the project:
```bash
python src/main.py
```

### 6. Commit Your Changes
```bash
git add .
git commit -m "Add [tool name] tool"
```
If others contributed to this tool (e.g., collaborative development), add a `Co-authored-by` tag at the end of the commit message (see "Co-Authors" below).

### 7. Push to Your GitHub Repository
```bash
git push origin add-tool-name
```

### 8. Create a Pull Request
- Open your fork on GitHub and click **Compare & pull request**.
- Write a clear title and description explaining your tool’s functionality, usage examples, etc.
- Click **Create pull request**.

### 9. Wait for Review
Maintainers will review your PR and may suggest changes. You can push further updates to the same branch, and the PR will update automatically.

---

## 🧠 Skill Contribution
FranxAgent supports loading extra knowledge, rules, or workflows (Markdown files) via the `knowledge/` folder. You can contribute practical skills to help the AI perform better in specific task domains.

### 1. Fork the Repository (Same as Above)

### 2. Clone Your Fork Locally (Same as Above)

### 3. Create a New Branch
```bash
git checkout -b add-skill-name
```
Example: `add-research-workflow`.

### 4. Add Skill Files
Add a `.md` file on the `skills` branch (remember to mark `(Skill)` in the document title).
The file should include:

- **Title** (level-3 heading, e.g., `### Academic Research Workflow`)
- **Overview**: A brief description of the skill’s purpose
- **Disclaimer** (optional): Include a disclaimer if the skill involves domain-specific risks
- **Main Content**: Clear steps, rules, or examples, structured using Markdown heading levels (`##`, `###`, `####`)
- **Usage Suggestions**: Instructions for how the AI or user can utilize this skill
- **License**: Skill files must be released under the **GNU Free Documentation License (GFDL) 1.3 or later**. Include a copyright notice at the top of the file in this format:
  ```markdown
  <!--
  Copyright (C) 2026 Author Name
  See the file COPYING for copying conditions.
  -->
  ```
  Ensure the repository root includes the GFDL license text (`COPYING` file).

**Requirements**:
- File encoding must be UTF-8.
- Content must be practical, avoid overly vague or duplicated existing knowledge.
- Must not contain any content that violates laws, infringes on others’ rights, or is sensitive.

### 5. Local Verification
Run FranxAgent locally to confirm the skill loads correctly (the console prints a list of loaded skill files on startup).
If the skill content is valid, the AI will exhibit corresponding behavior in conversations.

### 6. Commit Your Changes
```bash
git add your-skill-file.md
git commit -m "Add [skill name] skill"
```
For collaborative work, use the `Co-authored-by` tag as needed.

### 7. Push to Your GitHub Repository (Same as Above)

### 8. Create a Pull Request
- Set the target branch to **skills**
- Example title: `Add academic research workflow skill`
- In the description, briefly explain the skill’s purpose, scope, and usage examples.

### 9. Wait for Review
Maintainers will review the skill for logic, formatting, and completeness. Feedback for improvements will be provided in the PR if needed.

---

## 🧑‍🤝‍🧑 Co-Authors
If you collaborated with partners on development or wish to credit others’ contributions, use this format in your commit message (**must be on its own line; email must be linked to GitHub**):

```bash
git commit -m "Add weather tool

Co-authored-by: Partner Username <partner-email>"
```

GitHub will display both your and your partner’s avatars on the commit.

---

## 📝 Code Style
- Python code follows PEP 8 standards, though strict compliance is not required as long as clarity is maintained.
- Use descriptive names for functions and variables.
- Add necessary comments, especially for complex logic.

---

## 🧪 Testing
- If possible, add simple tests for your tool (a testing framework will be introduced in the future).
- For now, ensure your tool works properly when running `src/main.py` locally.

---

## 🔀 Resolving Conflicts
If your PR has merge conflicts (usually due to branch updates during your submission):
1. Add the official FranxAgent repository as a remote:
   ```bash
   git remote add upstream https://github.com/xhdlphzr/FranxAgent.git
   ```
2. Fetch the latest code:
   ```bash
   git fetch upstream
   ```
3. Merge into your branch:
   ```bash
   git checkout add-tool-name
   git merge upstream/main
   ```
4. Resolve conflicts (Git will indicate conflicting files), then commit and push.

If you are unfamiliar with conflict resolution, leave a comment in the PR and maintainers will assist.

---

## 💬 Other Contributions
- **Documentation Improvements**: Directly edit `README.md` or `CONTRIBUTING.md` and submit a PR.
- **Bug Reports**: Open a new Issue on the Issues page with clear reproduction steps and environment details.
- **Feature Suggestions**: Submit proposals via Issues as well.

---

## 🎉 Acknowledgments
Thank you for contributing to FranxAgent! Every line of code and every piece of knowledge makes this project better. If you run into any issues, feel free to ask questions in PRs or Issues.

Happy coding!