# 贡献指南

感谢你对 EasyMate 的兴趣！我们欢迎任何形式的贡献，包括新功能、工具插件、文档改进、Bug 报告等。为了让协作更顺畅，请遵循以下流程和规范。

## 📦 工具贡献（最常用）

如果你想为 EasyMate 添加一个新工具（例如 `weather`、`calc` 等），请按以下步骤操作：

### 1. Fork 仓库
- 访问 [EasyMate 仓库](https://github.com/MateUnion/EasyMate)，点击右上角的 **Fork**，将仓库复制到你的 GitHub 账户下。

### 2. 克隆你的 Fork 到本地
```bash
git clone https://github.com/你的用户名/EasyMate.git
cd EasyMate
```

### 3. 创建新分支
```bash
git checkout -b add-工具名
```
例如 `add-weather`。

### 4. 添加工具文件
在 `tools/` 目录下创建一个以工具名称命名的文件夹（例如 `tools/weather/`）。  
该文件夹必须包含以下三个文件：

#### a. `tool.py`
- 必须包含一个名为 `execute` 的函数，接收关键字参数（与 `config.json` 中的 `properties` 一致），并返回字符串结果。
- 示例：
  ```python
  def execute(city: str) -> str:
      # 实现天气查询逻辑
      return f"{city} 的天气是晴天，25℃"
  ```

#### b. `config.json`
- 定义工具的 OpenAI 函数调用格式，必须包含 `type` 和 `function` 字段。
- 示例：
  ```json
  {
    "type": "function",
    "function": {
      "name": "weather",
      "description": "获取指定城市的天气",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "城市名称"
          }
        },
        "required": ["city"]
      }
    }
  }
  ```

#### c. `README.md`
- 用简洁的格式说明工具的用途、输入、输出和注意事项（模仿已有工具）。
- 示例见 `tools/time/README.md`。

### 5. 本地测试
确保你的工具能正常导入并工作（可以临时修改 `src/main.py` 测试）。  
运行项目：
```bash
python src/main.py
```

### 6. 提交你的改动
```bash
git add tools/你的工具名/
git commit -m "添加 [工具名] 工具"
```
如果此工具有其他人的贡献（例如合作开发），请在提交信息末尾添加 `Co-authored-by`（见下文“共同作者”说明）。

### 7. 推送到你的 GitHub 仓库
```bash
git push origin add-工具名
```

### 8. 创建 Pull Request
- 在 GitHub 上打开你的 fork，点击 **Compare & pull request**。
- 填写清晰的标题和描述，说明你的工具功能、使用示例等。
- 点击 **Create pull request**。

### 9. 等待审查
维护者会审查你的 PR，可能会提出修改意见。你可以在同一分支上继续推送更新，PR 会自动更新。

---

## 🧑‍🤝‍🧑 共同作者（Co-authored-by）
如果你在开发过程中有伙伴一起贡献，或者你想保留他人的贡献记录，请在提交信息中使用以下格式（**必须独占一行，邮箱需为 GitHub 关联邮箱**）：

```bash
git commit -m "添加天气工具

Co-authored-by: 伙伴用户名 <伙伴邮箱>"
```

GitHub 会在该提交上同时显示你和伙伴的头像。

---

## 📝 代码风格
- Python 代码遵循 PEP 8 标准，但不必过于严苛，保持清晰即可。
- 函数、变量命名应具有描述性。
- 添加必要的注释，尤其是复杂逻辑。

---

## 🧪 测试
- 如果可能，为你的工具添加简单的测试（未来会引入测试框架）。
- 目前至少确保在本地运行 `src/main.py` 能正常调用你的工具。

---

## 🔀 处理冲突
如果你的 PR 出现了冲突（通常是因为 `main` 分支在你提交期间有了新变化），可以：
1. 将 EasyMate 官方仓库添加为远程：
   ```bash
   git remote add upstream https://github.com/MateUnion/EasyMate.git
   ```
2. 获取最新代码：
   ```bash
   git fetch upstream
   ```
3. 合并到你的分支：
   ```bash
   git checkout add-工具名
   git merge upstream/main
   ```
4. 解决冲突（Git 会提示哪些文件冲突），然后提交并推送。

如果你不熟悉冲突解决，可以在 PR 中留言，维护者会协助。

---

## 💬 其他贡献
- **文档改进**：直接修改 `README.md` 或 `CONTRIBUTING.md`，提交 PR。
- **Bug 报告**：在 Issues 页面创建新 Issue，描述清楚复现步骤和环境。
- **功能建议**：同样通过 Issues 提出。

---

## 🎉 感谢
感谢你愿意为 EasyMate 贡献！你的每一行代码都会让这个项目变得更好。如果遇到任何问题，欢迎在 PR 或 Issue 中提问。

Happy coding!