# 贡献指南

[English](../CONTRIBUTING.md) | **中文**


感谢你对 FranxAgent 的兴趣！我们欢迎任何形式的贡献，包括新功能、工具插件、**技能**、文档改进、Bug 报告等。为了让协作更顺畅，请遵循以下流程和规范。

---

## 📦 工具贡献（最常用）

如果你想为 FranxAgent 添加一个新工具（例如 `weather`、`calc` 等），请按以下步骤操作：

### 1. Fork 仓库
- 访问 [FranxAgent 仓库](https://github.com/xhdlphzr/FranxAgent)，点击右上角的 **Fork**，将仓库复制到你的 GitHub 账户下。

### 2. 克隆你的 Fork 到本地
```bash
git clone https://github.com/xhdlphzr/FranxAgent.git
cd FranxAgent
```

### 3. 创建新分支
```bash
git checkout -b add-工具名
```
例如 `add-weather`。

### 4. 添加工具文件
在 `tools` 分支下创建一个以工具名称命名的文件夹（例如 `weather/`）。  
该文件夹必须包含以下两个文件：

#### a. `tool.py`
- 必须包含一个名为 `execute` 的函数，接收关键字参数，并返回字符串结果。
- 示例：
  ```python
  def execute(city: str) -> str:
      # 实现天气查询逻辑
      return f"{city} 的天气是晴天，25℃"
  ```

#### b. `README.md`
- 用简洁的格式说明工具的用途、输入、输出和注意事项（模仿已有工具）。
- 示例见 `main` 分支中 `knowledge/tools/time/README.md`。

### 5. 本地测试
确保你的工具能正常导入并工作（可以临时修改 `src/main.py` 测试）。  
运行项目：
```bash
python src/main.py
```

### 6. 提交你的改动
```bash
git add .
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

## 🧠 技能贡献

FranxAgent 支持通过 `knowledge/` 文件夹加载额外的知识、规则或工作流（Markdown 文件）。你可以贡献一个实用的技能，帮助 AI 更好地完成特定领域的任务。

### 1. Fork 仓库（同上）

### 2. 克隆你的 Fork 到本地（同上）

### 3. 创建新分支
```bash
git checkout -b add-技能名
```
例如 `add-research-workflow`。

### 4. 添加技能文件
在 `skills` 分支下添加一个 `.md` 文件（在内容的标题中记得标注 `（技能）` ）。  
该文件应包含以下内容：

- **标题**（使用三级标题，例如 `### 科研工作流程`）
- **概述**：简要说明技能的作用
- **免责声明**（可选）：如果技能涉及特定领域风险，请添加免责声明
- **主体内容**：清晰的步骤、规则或示例，格式建议使用 Markdown 的标题层级（`##`、`###`、`####`）组织
- **使用建议**：告诉 AI 或用户如何利用该技能
- **许可证**：技能文件需采用 **GNU Free Documentation License (GFDL) 1.3** 或更高版本发布。请在文件头部添加版权声明，格式如下：
  ```markdown
  <!--
  Copyright (C) 2026 作者名
  See the file COPYING for copying conditions.
  -->
  ```
  确保仓库根目录已包含 GFDL 许可证文本（`COPYING` 文件）。

**要求**：
- 文件编码为 UTF-8。
- 内容应具有实用性，避免过于笼统或重复已有知识。
- 请确保不包含任何违反法律法规、侵犯他人权益或敏感的内容。

### 5. 本地验证
你可以在本地运行 FranxAgent，观察技能是否被正常加载（启动时控制台会打印已加载的技能文件列表）。  
如果技能内容正确，AI 在对话中会表现出相应的行为。

### 6. 提交你的改动
```bash
git add 你的技能文件.md
git commit -m "添加 [技能名] 技能"
```
如有多人合作，同样可以使用 `Co-authored-by`。

### 7. 推送到你的 GitHub 仓库（同上）

### 8. 创建 Pull Request
- 目标分支选择 **skills**
- 标题示例：`添加科研工作流程技能`
- 描述中请简要说明技能的用途、适用范围以及使用示例。

### 9. 等待审查
维护者会审查技能内容的合理性、格式规范等。如果有改进建议，会在 PR 中反馈。

---

## 🧑‍🤝‍🧑 共同作者（Co-authored-by）
如果你在开发过程中有伙伴一起贡献，或者你想保留他人的贡献记录，请在提交信息中使用以下格式（**必须独占一行，邮箱需为 GitHub 关联邮箱**）：

```bash
git commit -m "添加天气工具

Co-authored-by: 伙伴用户名 <伙伴邮箱>"
```

GitHub 会在该提交上同时显示你和伙伴的头像。

---

## 添加翻译

FranxAgent 使用基于 YAML 的国际化方案。添加新语言步骤如下：

### 1. 创建 YAML 文件

将 `i18n/en.yaml` 复制为 `i18n/<lang>.yaml`（例如日语为 `i18n/ja.yaml`），然后翻译所有值。

### 2. YAML 结构

```yaml
config:
  language: "Sprache"          # 只翻译值
  api_key: "API-Schlüssel"
```

- **不要**翻译键名（如 `config.language`）——它们是代码标识符
- **不要**翻译值中的 `{占位符}`——例如 `{name}`、`{message}` 必须原样保留
- **不要**翻译 Emoji 前缀——例如 `📸`、`⏰`、`💾` 保持不变

### 3. 添加语言选项

在 `src/templates/index.html` 的语言选择器中添加 `<option>`：

```html
<select id="language">
    <option value="en">English</option>
    <option value="zh">中文</option>
    <option value="ja">日本語</option>  <!-- 添加这行 -->
</select>
```

### 4. 启用语言

在 `config.json` 中设置 `"language": "ja"`，或在配置页面选择。

### 5. 验证

- 所有 UI 文本应显示为新语言
- `{name}` 等占位符必须正确渲染（检查工具调用块、错误消息）
- 检查配置页、登录页和注册页
- 如果缺少某个键，键名本身将作为回退显示

### 备注

- 回退顺序：`<lang>.yaml` → `en.yaml` → 原始键名
- 如果 `config.json` 中缺少 `language` 字段，默认为 `en`
- 保持翻译简洁——移动端 UI 空间有限

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
如果你的 PR 出现了冲突（通常是因为分支在你提交期间有了新变化），可以：
1. 将 FranxAgent 官方仓库添加为远程：
   ```bash
   git remote add upstream https://github.com/xhdlphzr/FranxAgent.git
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
感谢你愿意为 FranxAgent 贡献！你的每一行代码和每一份知识都会让这个项目变得更好。如果遇到任何问题，欢迎在 PR 或 Issue 中提问。

Happy coding!