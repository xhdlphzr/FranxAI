<!--
This is part of FranxAI
Copyright (C) 2026 xhdlphzr
See the file COPYING for copying conditions.
-->

# Research Process (Skill) | 科研流程 (技能)

**Core Principles**: Execute strictly by stages, no skipping or tampering. Prohibit academic fraud (data, charts, literature, derivations). Label "theoretical research" when no real experiments are conducted.

---

#### Stage 1: Material Selection

**Objective**: Determine specific, verifiable research questions, prepare basic data and tools.

- **Topic Selection**: Focus on a specific scenario, clarify pain points (e.g., low efficiency, poor accuracy), assess feasibility (using open-source tools/public data, single stage ≤7 days). Write research question in 1-2 sentences.
- **Background Research**: List 3-4 common methods and their limitations, identify 1-2 implementable innovations.
- **Material Preparation**: Use public datasets or generate simulated data (specify rules). Identify 3-5 open-source tools, create folder structure `research/{data,code,docs}`.

**Output**: Research proposal, background notes, dataset list.

---

#### Stage 2: Review

**Objective**: Self-review research design, identify logical and feasibility gaps.

- **Design Review**: Verify problem clarity, experimental logic, data compliance, innovation points, and tool compatibility.
- **Feasibility Verification**: Small-scale pilot experiments, estimate resources, list risks and countermeasures.

**Output**: Review report, adjusted design, risk list.

---

#### Stage 3: Coding

**Objective**: Implement runnable code, fully document experimental process.

- **Environment Setup**: Configure Python environment, initialize Git, write `code/README.md`, fix random seeds.
- **Core Implementation**: Modular code (data reading, core methods, experiments, output), add comments and exception handling.
- **Experiment Execution**: Run step by step, record logs (parameters, output, exceptions), repeat 2-3 times to verify stability, save charts.

**Output**: Code repository, experiment logs, result charts.

---

#### Stage 4: Writing

**Objective**: Write authentic, complete Markdown paper according to fixed structure.

**Structure**:
- Title, abstract, research direction review, introduction, research methods, experimental results and analysis, result review, conclusion and future work, appendix

**Content Requirements**:
- Abstract: Background, methods, **real results**, significance
- Introduction: Scenario, limitations, contributions, chapter arrangement
- Methods: Core ideas, step parameters, reproducibility instructions
- Experiments: Setup, **real data/charts**, analysis (including limitations)
- Conclusion: Achievements, shortcomings, future directions

**Output**: Markdown paper, charts, optional PDF/HTML.

---

#### Stage 5: Final Review

**Objective**: Comprehensive self-check of paper and code, correct issues.

- **Self-Review**: Check reproducibility, data authenticity, logical coherence, format standards, academic integrity (no fabrication).
- **Revision**: Categorize and record issues, correct them one by one, polish language.

**Output**: Revised paper, issue correction list, final code/logs.

---

**核心原则**：严格按阶段执行，不得跳过或篡改。禁止学术造假（数据、图表、文献、推导）。无真实实验时标注“理论研究”。

#### 阶段一：选材

**目标**：确定具体、可验证的研究问题，准备基础数据与工具。

- **选题**：聚焦一个细分场景，明确痛点（如效率低、精度差），评估可行性（使用开源工具/公开数据，单阶段≤7天）。用1-2句话写出研究问题。
- **背景梳理**：列出3-4种常见方法及其局限，确定1-2个可落地的创新点。
- **材料准备**：使用公开数据集或生成模拟数据（注明规则）。确定3-5个开源工具，创建文件夹结构 `research/{data,code,docs}`。

**产出**：研究计划书、背景笔记、数据集清单。

---

#### 阶段二：审核

**目标**：自我评审研究设计，排查逻辑与可行性漏洞。

- **设计评审**：验证问题清晰性、实验逻辑、数据合规性、创新点与工具兼容性。
- **可行性验证**：小规模预实验，估算资源，列出风险与应对。

**产出**：评审报告、调整后的设计、风险清单。

---

#### 阶段三：编码

**目标**：实现可运行代码，完整记录实验过程。

- **环境搭建**：配置Python环境，初始化Git，编写 `code/README.md`，固定随机种子。
- **核心实现**：模块化代码（数据读取、核心方法、实验、输出），添加注释与异常处理。
- **实验执行**：分步运行，记录日志（参数、输出、异常），重复2-3次验证稳定性，保存图表。

**产出**：代码仓库、实验日志、结果图表。

---

#### 阶段四：写文

**目标**：按固定结构撰写真实、完整的Markdown论文。

**结构**：
- 标题、摘要、研究方向审核、引言、研究方法、实验结果与分析、结果审核、结论与未来工作、附录

**内容要求**：
- 摘要：背景、方法、**真实结果**、意义
- 引言：场景、局限、贡献、章节安排
- 方法：核心思路、步骤参数、可复现说明
- 实验：设置、**真实数据/图表**、分析（含局限性）
- 结论：成果、不足、未来方向

**产出**：Markdown论文、图表、可选PDF/HTML。

---

#### 阶段五：审核

**目标**：全面自查论文与代码，修正问题。

- **自我评审**：检查可复现性、数据真实性、逻辑连贯性、格式规范、学术诚信（无伪造）。
- **修改**：分类记录问题，逐条修正，润色语言。

**产出**：修订版论文、问题修改清单、最终代码/日志。