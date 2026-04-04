# Contribution Guide

Thank you for your interest in FranxAI! We welcome all forms of contributions, including new features, tool plugins, skills, documentation improvements, bug reports, and more. Please follow the processes and specifications below to ensure smooth collaboration.

---

## 📦 Tool Contribution (Most Common)

If you want to add a new tool to FranxAI (such as `weather`, `calc`, etc.), please follow these steps:

### 1. Fork the Repository
- Visit the [FranxAI Repository](sslocal://flow/file_open?url=https%3A%2F%2Fgithub.com%2Fxhdlphzr%2FFranxAI&flow_extra=eyJsaW5rX3R5cGUiOiJjb2RlX2ludGVycHJldGVyIn0=) and click the **Fork** button in the upper right corner to copy the repository to your GitHub account.

### 2. Clone Your Fork Locally
```bash
git clone https://github.com/xhdlphzr/FranxAI.git
cd FranxAI
```

### 3. Create a New Branch
```bash
git checkout -b add-tool-name
```
For example: `add-weather`.

### 4. Add Tool Files
Create a folder named after the tool within the `tools/` directory (e.g., `tools/weather/`).
This folder must contain the following two files:

#### a. `tool.py`
- It must include a function named `execute` that accepts keyword arguments and returns results in string format.
- Example:
  ```python
  def execute(city: str) -> str:
      # Implement weather query logic
      return f"The weather in {city} is sunny with a temperature of 25°C"
  ```

#### b. `README.md`
- Briefly explain the tool's purpose, input parameters, output format and notes following the style of existing tools.
- Refer to `knowledge/tools/time/README.md` for examples.

### 5. Local Testing
Make sure your tool can be imported and run normally (you may modify `src/main.py` temporarily for testing purposes).
Run the project with the following command:
```bash
python src/main.py
```

### 6. Commit Your Changes
```bash
git add tools/your-tool-name/
git commit -m "Add [Tool Name] tool"
```
If other contributors participated in developing this tool, add the `Co-authored-by` statement at the end of the commit message (see the "Co-Author" section below).

### 7. Push to Your GitHub Repository
```bash
git push origin add-tool-name
```

### 8. Create a Pull Request
- Open your forked repository on GitHub and click **Compare & pull request**.
- Fill in a clear title and description, explaining the tool's functions and usage examples.
- Click **Create pull request**.

### 9. Wait for Review
Maintainers will review your pull request and may put forward revision suggestions. You can push updates to the same branch, and the pull request will be updated automatically.

---

## 🧑‍💻 Skill Contribution

FranxAI loads additional knowledge, rules and workflows (Markdown files) through the `knowledge/` folder. You can contribute practical skills to help the AI complete tasks in specific fields more effectively.

### 1. Fork the Repository (Same as Above)

### 2. Clone Your Fork Locally (Same as Above)

### 3. Create a New Branch
```bash
git checkout -b add-skill-name
```
For example: `add-research-workflow`.

### 4. Add Skill Files
Add a `.md` file under the `knowledge/skills/` directory (mark **(Skill)** in the title of the document).
The file needs to include the following content:

- **Title** (First-level heading, e.g., `# Academic Research Workflow`)
- **Overview**: Briefly describe the function of the skill
- **Disclaimer** (Optional): Add a disclaimer if the skill involves risks in specific fields
- **Main Content**: Present clear steps, rules or examples, organized with Markdown heading levels (`##`, `###`, `####`)
- **Usage Guidelines**: Explain how AI or users can use this skill
- **License**: Skill files must be released under the **GNU Free Documentation License (GFDL) 1.3** or later versions. Add a copyright notice at the top of the file in the following format:
  ```markdown
  <!--
  Copyright (C) 2026 Author Name
  See the file COPYING for copying conditions.
  -->
  ```
  Ensure the GFDL license text file (`COPYING`) exists in the root directory of the repository.

**Requirements**:
- The file encoding must be UTF-8.
- The content must be practical, avoiding vague descriptions or duplication of existing knowledge.
- The content must not contain any illegal, infringing or sensitive information.

### 5. Local Verification
Run FranxAI locally to check whether the skill is loaded successfully (the console will print the list of loaded skill files on startup).
If the skill content is correct, the AI will show corresponding behavioral changes in conversations.

### 6. Commit Your Changes
```bash
git add your-skill-file.md
git commit -m "Add [Skill Name] skill"
```
Use the `Co-authored-by` tag for collaborative contributions when needed.

### 7. Push to Your GitHub Repository (Same as Above)

### 8. Create a Pull Request
- Select **skills** as the target branch
- Example title: `Add academic research workflow skill`
- Briefly explain the skill's purpose, applicable scope and usage examples in the description.

### 9. Wait for Review
Maintainers will review the rationality and formatting of the skill content, and provide feedback in the pull request if revisions are needed.

---

## 🤝 Co-Author Specification
If you collaborate with partners during development or need to record other contributors, use the following format in commit messages (must occupy an independent line, and the email must be bound to your GitHub account):

```bash
git commit -m "Add weather tool

Co-authored-by: Partner Username <partner-email-address>"
```

GitHub will display the avatars of all relevant contributors under this commit.

---

## 📝 Code Style
- Python code follows the PEP 8 standard; strict compliance is not required as long as readability is guaranteed.
- Use descriptive names for functions and variables.
- Add necessary comments for complex logic.

---

## 🧪 Testing
- Add simple test cases for your tool if possible (a formal testing framework will be introduced in the future).
- Currently, ensure your tool can be called normally by running `src/main.py` locally.

---

## 🔀 Resolving Merge Conflicts
If merge conflicts appear in your pull request (usually caused by updates to the `main` branch during your development):
1. Add the official FranxAI repository as a remote source:
   ```bash
   git remote add upstream https://github.com/xhdlphzr/FranxAI.git
   ```
2. Fetch the latest code:
   ```bash
   git fetch upstream
   ```
3. Merge updates into your branch:
   ```bash
   git checkout add-tool-name
   git merge upstream/main
   ```
4. Resolve conflicts according to Git prompts, then commit and push your changes.

If you are not familiar with conflict resolution, leave a message in the pull request, and maintainers will offer assistance.

---

## 💬 Other Contributions
- **Documentation Optimization**: Modify `README.md` or `CONTRIBUTING.md` directly and submit a pull request.
- **Bug Reports**: Create a new Issue with detailed reproduction steps and operating environment information.
- **Feature Suggestions**: Submit proposals through Issues.

---

## 🎉 Acknowledgments
Thank you for contributing to FranxAI! Every line of code and every piece of knowledge you provide will make this project better. Feel free to ask questions in pull requests or Issues if you encounter any problems.

Happy coding!