# 曾屹荣 · 简历内容整理（基于 CV/ 两份 docx 草稿）

> **本文件不参与构建，只是溯源存档。** 它是最初从 docx 草稿整理出的内容底稿（人读、追溯用）。
> 参与构建的数据在 `build/data/` 下的三份 YAML（A/B/C 各一份，不共享字段）；
> 要改简历请改那里，改完跑 `python build.py` 与 `python build/validate.py`。
> 若本文件与数据文件冲突，**以数据文件为准**——这里记录的是「当初为什么这么写」，
> 而不是「现在写的是什么」。

> 用途：人才计划求职简历的内容底稿。信息以 `zeng-yirong_resume_optimized_v3.docx`（结构化优化版）为主，
> `zeng-yirong_resume_all.docx`（原始完整版）为补充校验来源。

---

## 1. 基本信息
- **姓名**：曾屹荣（Yirong Zeng）
- **定位**：博士候选人 · Agentic RL / 大模型工具学习 / Harness Agent 训练
- **学校/专业**：哈尔滨工业大学（本部）计算学部 · 计算机科学与技术 · 直博五年级（2022.09 入学，预计 2027.09 毕业）
- **导师**：刘挺教授（校长）；**实验室**：社会计算与交互机器人研究中心（SCIR）
- **本科**：哈尔滨工程大学 · 计算机科学与技术（2018.09–2022.07）
- **联系方式**：18845723437 | yrzeng@ir.hit.edu.cn
- **链接**：主页 zeng-yirong.github.io | Google Scholar | GitHub.com/zeng-yirong

## 2. 核心亮点（数字速览）
| 指标 | 数值 |
|---|---|
| 一作已发表论文 | **9 篇**（CCF-A 4：NeurIPS'26×2、ICLR'26、ACL'26；CCF-B 4：EMNLP'25×2、NAACL'25、COLING'24；SCI-Q1 1：IPM'26） |
| CCF-A 在投 | **6 篇**（ICLR'27×4、AAAI'27 Phase II、ACL-ARR） |
| 华为实习成果 | 12 项研究成果，**4 项落地小艺业务** |
| 团队角色 | 首批顶尖人才计划实习生 · 部门实习生领头人（带 7 人团队） |
| 代表性量化 | 指令遵从 81→89；训练资源开销 ↓8×；推理开销 ↓32%；SFT 数据 2 万条/42 类场景；139 个 RL 环境；TinyJudge 平均性能 +10%、奖励精度 +12%、训练速度 3× |
| 开源 | ClawLoop ⭐33、ClawForge/EnvCraft ⭐32、MIFS 数据集 11k+ downloads |

## 3. 实习经历（重点板块）
**华为（北京）小艺 · 基础算法开发部 | 研究型实习生 | 2024.09–至今**
- ▸ **Harness Agent 训练体系搭建**：SFT 数据流水线（2w 条、42 类场景，NeurIPS'26）；主导 139 个 Agentic RL Tool 环境（EnvCraft ICLR'27 在投 / ClawForge 开源）；轻量化 Harness 支撑 In-Harness RL（开销 ↓8×、推理 ↓32%，AAAI'27 / ClawLoop 开源）
- ▸ **Agentic RL 核心算法**：解耦熵约束 AutoTool（ICLR'26，落地小艺主对话快慢思考）；无效交互截断+token 掩码提升训练稳定性（NeurIPS'26）；昇腾生态适配、信用分配（iTool EMNLP'25）
- ▸ **指令遵循**：反馈信号质量瓶颈 → 约束密度控制，81→89 落地小艺主对话（ICLR'27 在投）；TinyJudge 轻量专家集成缓解 reward hack（ACL'26）；OPD 解耦-聚合 +4%（ICLR'27 在投）

## 4. 研究方向
1. **Agentic RL**（2024.09–今）：训练稳定性与上限、自适应快慢思考、工具环境/数据合成、轻量 Harness 与 In-Harness RL；近期探索 Skill Curator 实现 Agent Skill 进化
2. **Instruction Following**（2025.06–今）：RL 下泛化性机制、多模态 RLVR 数据合成（MIFS）、OPD 应用

## 5. 论文清单
### 已发表（一作 9 篇）
1. Unveiling Entropy-Performance Decoupling in Agentic RL — **NeurIPS 2026 (CCF-A)**
2. ClawBenchPro: Benchmarking Agent Harnesses（共一）— **NeurIPS 2026 (CCF-A)**
3. AutoTool: Decoupled Entropy Constraints — **ICLR 2026 (CCF-A)**，落地小艺
4. TinyJudge: Lightweight Specialist Ensembles — **ACL 2026 (CCF-A)**
5. iTool: Dynamic Deficiency Calibration — **EMNLP 2025 Main (CCF-B)**
6. Tool Zero: Pure RL from Scratch — **EMNLP 2025 Findings (CCF-B)**，业界首篇
7. Moderation Matters: Rumor Detection — **NAACL 2025 (CCF-B)**
8. RU22Fact: Multilingual Fact-Checking — **COLING 2024 (CCF-B)**
9. Human Cognitive Aligned Rumor Detection — **IPM 2026**（本人 2026-09-30 定：等级只由 SCI-Q1 标签表达，`venue` 里不再重复写 `(SCI-Q1)`；也不再算 CCF-B）

### 在投（CCF-A 6 篇）
10. Precision Bounds Diversity: Reward Engineering for IF — ICLR 2027
11. EnvCraft: Synthesizing Executable Environments — ICLR 2027
12. Constraint-Decoupled OPD for Multi-Constraint IF — ICLR 2027
13. Less Harness, More Signal（共一）— AAAI 2027 Phase II
14. Not Every Tool Call Helps（共一）— ICLR 2027
15. Towards Scalable RLVR: Multimodal IF（MIFS）— ACL-ARR

## 6. 荣誉奖项
- **中国科协青年科技人才培育工程博士生专项计划**（2026）★人才计划强相关
- **华为火花奖**（agent skill 渐近式披露 + 指令遵循泛化性探索）
- 教育部国家奖学金；各级校级奖学金
- ACM 省赛银牌（队长，2021）；全国数学竞赛二等奖（2020）；数学建模一等奖（2019）

## 7. 开源项目 / 其他
- ClawLoop（Verla 上的轻量 Harness 训练框架）⭐33；ClawForge/EnvCraft ⭐32；MIFS 数据集 11k+ downloads
- 惊堂木小程序（虚假信息检测，主导开发，2025.01）；活字大模型开源贡献（⭐200+，2024）

---

## 排版建议（针对"人才计划"评审场景）
1. **一页纸原则的取舍**：内容量大，建议主简历 1–2 页；论文可压缩为紧凑列表（标题加粗 + venue 徽章），摘要级说明只保留 3 篇代表作。
2. **突出人才计划匹配点**：科协博士生专项、国家奖学金、华为顶尖人才计划、火花奖应前置到显眼位置（头部徽章条或独立荣誉区）。
3. **量化优先**：81→89、↓8×、12 项成果/4 项落地等数字用高亮样式呈现。
4. **照片使用**：CV/personal-photo.jpg 适合放侧栏或页眉（学术风可不放，企业/人才计划风建议放）。
