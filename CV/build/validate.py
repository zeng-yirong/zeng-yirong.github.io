#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三份数据的事实一致性校验（防漂移）。

A/B/C 各自独立，同一批事实因此写了三遍——代价是将来可能只改了其中一份。
本脚本刻意**不关心三份文件的 schema**（那正是它们应该不同的地方），只做两件事：

  1) 集合一致：把每份 YAML 里所有字符串标量当事实清单，断言三份的事实集合相同。
     这是自动推导的，不写死，因此覆盖面是全量而非抽样。
     **例外**：C 版措辞自 2026-09-28 起由本人单独重写，与 A/B 必然不同，
     故对 C 只报告差异、不判失败（A↔B 仍逐字对齐）。C 的事实覆盖由第 2 条保证。
  2) 地标事实：手写一份「绝不能被弄丢」的清单（论文/荣誉/学校/项目/开源/关键数字），
     断言每项在三份中都出现——第 1 条查不出「三份一起删掉」的情况，这条能，
     也是 C 版事实不丢的主要保障。

  --check-html：对每份产物 HTML 跑第 2 条同一份清单，断言「数据里写了的，页面上看得见」
     ——这是唯一能抓到模板漏渲染某段事实的检查。

用法：
  python validate.py                # 三份数据事实一致
  python validate.py --check-html   # 再加：渲染结果没漏事实

版本专属字符串（只该出现在一份里）记录在 ONLY_IN，每条都要写明理由；
不要把新出现的差异往里加——先确认它是不是漏改。
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT     = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_HTML = ROOT / "output" / "html"

DATA = {"A": "A-general.yaml", "B": "B-institute.yaml", "C": "C-talent.yaml"}
HTML = {"A": "resume-A-general.html", "B": "resume-B-institute.html", "C": "resume-C-talent.html"}
LABEL = {"A": "通用版", "B": "研究院版", "C": "人才计划版"}

# 段落名等结构性取值不是「事实」，参与比较只会产生噪音
STRUCTURAL = {
    "summary", "education", "internship", "research_focus", "publications",
    "opensource", "awards", "projects", "skills", "highlights",
    # 图标名 / 平台名：数据的 `icon:`/`logo:` 字段是「怎么画」的指令，不是事实。
    # 模板把它们换成内联 SVG（页面上看不到这串字），所以不该参与事实比较。
    "pubs", "research", "phone", "mail", "advisor", "lab",
    "home", "scholar", "github", "modelscope",
}
MIN_LEN = 6
# 数据自己的复合行分隔符。同一条事实在 A 里可能是两个字段、在 C 里被合成一行
# （如 degree+major -> "直博五年级 · 博士候选人 · 计算学部 · 计算机科学与技术"），
# 所以比较前先按这些符号切碎——允许重组，不允许丢失。
FRAG = re.compile(r"[·：；、｜]")

# 允许只出现在某一份里的字符串（豁免清单，是一个集合差集用的减数，不是「事实清单」）。
# 每一条都要写明理由；不要把新冒出来的差异往里加，先确认它是不是漏改。
# 这里记的都是「版面头衔/标语」——对事实层的再表述：三条实质事实（科协专项计划 /
# 顶尖人才计划实习生 / 国家奖学金）三份正文里都在。
ONLY_IN = {
    # A 已无豁免：2026-09-28 的 A/B→C 同步把 A 的 hero 标语改成了 C 的中文表述，
    # 原来那条「Agentic RL / 大模型工具学习 / Harness Agent 训练」三份都不再出现。
    # 留一个空集合是有意的——下一处真豁免要写进这里，别顺手把差异塞进别处。
    "A": set(),
    "B": {
        # B 独有的中英对照段落表头（A 的表头写死在模板、C 用中文 title；中文标题 <6 字不入清单）
        "RESEARCH INTERESTS", "PUBLICATIONS", "INDUSTRY EXPERIENCE", "EDUCATION",
        "OPEN SOURCE", "HONORS & AWARDS", "PROJECTS", "SKILLS",
        # 页眉徽章话术（A 的 title_chips 为空，侧栏不放头衔）
        "一作 9 篇（CCF-A×4）", "6 篇 CCF-A 在投", "Agentic RL · IF",
        # B 把毕业时间单列（"预计毕业：2027.09"），A/C 塞在学制括号里，故只有 B 有独立这一条
        "2027.09",
        # 2026-10-01：本人把这两项从 A 的「数字亮点」撤掉了（那条横条只有 A 显示），
        # A 的数据里已无这两个标签。B 的 highlights / C 的 kpis_hidden 仍各留一份
        # （两版本来就不渲染那条横条，留着是「保留事实」），于是它们从三份共有变成 B/C 独有。
        # 注意 A 只是不把这两个数字**当亮点陈列**：「12 项研究成果、4 项落地小艺」这句
        # 仍写在三份的实习 lead 里，所以 LANDMARKS 与第 2 节都不受影响。
        "华为研究成果", "成果落地小艺",
    },
    # C 原来还有 5 条豁免（hero 标语 + 教育条目上的 4 个短标签），2026-09-28 的
    # A/B→C 同步之后 A/B 也有了同样的标语与同一批徽章文字，它们从「C 独有」变成三份共有。
    # 现在 C 真正独有的是「实习身份那句话的写法」——它按 sw["body"] 渲染，
    # 与 A/B 的 sw["lead"] 不是同一个字段，第 1 节会把它报成 1 项差异，这是预期内的。
    "C": {
        # 段落标题是「怎么排」不是「事实」：C 把开源那一段叫「主导的开源项目」，
        # A/B 叫「开源项目」。落在数据里的是 C 的 rail.title，所以进了事实集合；
        # A/B 的标题写在 main_sections/sections 里（壳），不进集合。
        # 要统一的话改 A/B 的壳，不是改这里——这里只是别让它天天报警。
        "主导的开源项目",
        # 同 B：本人 2026-10-01 从 A 的数字亮点撤掉了这两项，C 的 kpis_hidden 仍保留
        "华为研究成果", "成果落地小艺",
    },
}

# 地标事实：弄丢任何一条都是事故。字符串按「归一化后的子串」匹配。
# 一条地标可以写成元组 = 允许各版用词不同（如 C 把 "2 万条" 写成 "2+ 万条"），
# 只要每一份**至少命中一种写法**就算通过——事实在，措辞随版本。
LANDMARKS = [
    # 15 篇论文（9 已发表 + 6 在投）
    "Unveiling Entropy-Performance Decoupling in Agentic RL for Tool-Integrated Reasoning",
    "ClawBenchPro: Benchmarking How Well Agent Harnesses Work",
    "AutoTool: Automatic Scaling of Tool-Use Capabilities in RL via Decoupled Entropy Constraints",
    "TinyJudge: Unverifiable Constraint Alignment via Lightweight Specialist Ensembles",
    "iTool: Reinforced Fine-Tuning with Dynamic Deficiency Calibration for Advanced Tool Use",
    "Tool Zero: Training Tool-Augmented LLMs via Pure RL from Scratch",
    "Moderation Matters: Exploring Large Language Models for Effective Rumor Detection on Social Media",
    "RU22Fact: Optimizing Evidence for Multilingual Explainable Fact-Checking on Russia-Ukraine Conflict",
    "Human Cognitive Process Aligned Rumor Detection with Small Language Models Enhanced Large Language Models",
    "Precision Bounds Diversity: Reward Engineering for Instruction Following via RLVR",
    "EnvCraft: Synthesizing Executable Environments in Agentic RL for Claw-like Agent",
    "Constraint-Decoupled On-Policy Distillation for Multi-Constraint Instruction Following",
    "Less Harness, More Signal: Efficient In-Harness RL for Autonomous Agents",
    "Not Every Tool Call Helps: Fine-Grained Credit Assignment for Efficient Tool-Integrated Reasoning",
    "Towards Scalable RLVR: Multimodal Instruction Following Data Synthesis and Distillation",
    # 6 项荣誉
    "中国科协青年科技人才培育工程博士生专项计划",
    "华为火花奖",
    "教育部国家奖学金；各级校级奖学金",
    "ACM 省赛银牌（队长）",
    "全国大学生数学竞赛二等奖",
    "全国大学生数学建模竞赛一等奖",
    # 实习：单位 + 3 个分组标题 + 领头人身份
    "华为（北京）小艺 · 基础算法开发部",
    "Harness Agent 训练体系搭建",
    "Agentic RL 算法研发",          # 2026-09-30 本人把三份的「核心算法研发」都删了「核心」二字
    "Agent 指令遵循性能提升",
    # A/B 写「带 7 人团队」；C 于 2026-09-28 改成「带 7 人实习生团队」（本人手改，语义更准）。
    # 一条地标允许各版用词不同，写成元组即可——两份都改之前别合并成一条。
    ("部门实习生领头人（带 7 人团队）", "部门实习生领头人（带 7 人实习生团队）"),
    # 教育 / 项目 / 开源
    "哈尔滨工业大学",
    "哈尔滨工程大学",
    "惊堂木 — 虚假信息检测系统小程序",
    "活字大模型开源项目",
    "ClawLoop",
    "ClawForge (EnvCraft)",
    "MIFS",
    # 研究方向两条主线
    "智能体强化学习（Agentic RL）",
    "指令遵循（Instruction Following）",
    # 联系方式与身份
    "18845723437",
    "yrzeng@ir.hit.edu.cn",
    "导师：刘挺教授（校长）",
    "社会计算与交互机器人研究中心（SCIR）",
    "2027.09",   # A/C 写在学制的括号里，B 单列「预计毕业：」——三种写法都必须还在
    # 关键数字（最容易在改写时被顺手改掉）
    "139",
    "81→89",
    "↓8×",
    "↓32%",
    ("2 万条", "2+ 万条"),
    "42 类",
    "11k+",
    "⭐ 33",
    "⭐ 60",   # ClawForge/EnvCraft；2026-09-30 本人把星数从 46 改成 60、时间 2026.07→2026.06
]

# 刻意不渲染的（数据里有、页面上没有），逐条写明理由，对应数据文件里的「# 未渲染」注释。
# 清单里的每一条都必须「真的没渲染」，否则第 3 条检查会报「豁免已失效」——
# 避免这份清单悄悄腐烂成一纸空文。
# 论文 note 被 note_hidden: true 隐藏时，那条文字在页面上就看不到了。三份数据里标的是
# 同一批 7 篇（本人 2026-09-29 要求 A/B 与 C 对齐：这几篇不必再介绍），所以列一次、三份共用。
# 事实保留在数据文件里，没有丢——将来想显示就删掉那篇的 note_hidden。
HIDDEN_NOTES = (
    "动态缺陷校准强化微调，复杂场景较基线提升 6.5%",
    "探索 LLM 在社交媒体谣言检测中的有效性，提出 moderation 增强方法",
    "多语言可解释事实验证，优化证据选择策略",
    "人类认知过程对齐的谣言检测，小模型增强大模型框架",
    "OPD 解耦-聚合修正教师多约束分布，性能 +4%",
    "细粒度信用分配，识别无效工具调用并优化工具集成推理效率",
    "多模态指令遵循 RLVR 数据合成与蒸馏，MIFS 数据集 11k+ downloads",
)

UNRENDERED = {
    # A 从 2026-09-29 起也有了「不渲染」的条目：论文的 note_hidden（见下 HIDDEN_NOTES）。
    "A": set(HIDDEN_NOTES),
    "B": {
        "一作已发表论文", "CCF-A 已发表", "华为研究成果",
        "成果落地小艺", "带教实习生(领头人)",   # highlights 的 label：学术版不放数字速览条
        "LLM Post-training",                 # chips：学术版页眉用 badges，不用关键词
        # 技能段：本人 2026-09-29 要求从 B 版面上撤掉（为把 PDF 压到 3 页），标记以注释留在
        # 产物里（开关是 sections 上那条 skills 的 comment_only）。注释里的字页面上看不到，
        # 所以这几条算「不渲染」。事实还在数据里，删掉开关就回来了。
        # 入清单的是「只在技能段出现」的字符串。「Instruction Following」「Agent Harness」
        # 虽然技能里有，但正文（研究方向标题 / 概要）也写着，所以页面上仍看得见——列进来会报
        # 「豁免已失效」。「中文」和「研究方向/技术栈/语言」这几个组名因为太短（<MIN_LEN）
        # 本来就不入事实集合，同样别列。
        "Agentic RL / RLVR", "Tool Learning",
        "Python/C++", "PyTorch", "Verl / veRL 训练框架", "GRPO / OPD / DPO",
        "华为昇腾 NPU", "English", "SKILLS",
        *HIDDEN_NOTES,
    },
    "C": {
        "LLM Post-training",                 # keywords：人才版 hero 用 badges，不用关键词
        "哈尔滨工业大学（本部）计算学部",        # hero.school_line：hero 行宽有限
        "华为研究成果", "成果落地小艺", "带教实习生(领头人)",   # kpis_hidden：数字条放不下的实习指标
        # 数字横条：本人 2026-09-28 要求不显示、但标记以注释留在产物里（kpis 数据仍在，
        # 开关是 kpis_comment_only）。注释里的字页面上看不到，所以这两个标签算「不渲染」。
        # 注意「CCF-A 在投」不在此列——正文（教育背景要点、summary）里写着它，所以它仍然
        # 可见，列进来会报「豁免已失效」。
        "一作已发表论文", "CCF-A 已发表",
        *HIDDEN_NOTES,
    },
}


def norm(s: str) -> str:
    """归一化：去行内标记、空白折叠成一个空格"""
    return re.sub(r"\s+", " ", (s or "").replace("**", "")).strip()


def walk_scalars(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            walk_scalars(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_scalars(v, out)


def flat_text(obj) -> str:
    """整份数据的归一化全文（用于地标子串匹配）"""
    out = []
    walk_scalars(obj, out)
    return norm(" ".join(out))


def facts(obj) -> set:
    out = []
    walk_scalars(obj, out)
    got = set()
    for s in out:
        for frag in FRAG.split(norm(s)):
            frag = frag.strip()
            if len(frag) >= MIN_LEN and frag not in STRUCTURAL:
                got.add(frag)
    return got


def html_haystack(path: Path) -> str:
    """产物正文：剥 <style>、剥标签，但保留属性值（链接只出现在 href 里）"""
    s = path.read_text(encoding="utf-8")
    s = re.sub(r"<style>.*?</style>", " ", s, flags=re.S)
    # HTML 注释不是渲染内容，必须剥掉：C 版刻意把数字横条的标记以注释留在产物里
    # （本人要求「不显示但别删，以后可能用到」），注释里的文字页面上看不到，
    # 不剥掉的话「豁免已失效」那条检查会把它们当成「其实渲染了」而误报。
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r'src="data:[^"]*"', " ", s)          # 内联照片 base64，没意义且极大
    attrs = re.findall(r'="([^"]*)"', s)
    # 标签必须「删掉」而不是「换成空格」：md() 会把 **xx** 渲染成 <em>xx</em>，
    # 换成空格就会得到 "产出 2 万条 数据"，与数据里的 "产出 2 万条数据" 对不上。
    s = re.sub(r"<[^>]+>", "", s)
    return norm(s + " " + " ".join(attrs))


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--check-html", action="store_true",
                    help="额外校验产物 HTML 没漏渲染事实")
    args = ap.parse_args()

    data = {k: yaml.safe_load((DATA_DIR / v).read_text(encoding="utf-8")) for k, v in DATA.items()}
    text = {k: flat_text(v) for k, v in data.items()}
    fs   = {k: facts(v) for k, v in data.items()}
    bad  = 0

    print("== 1. 三份数据的事实集合 ==")
    # A↔B 逐字对齐（漏改的主要来源），不一致即失败。
    # C 曾经是例外：2026-09-28 本人单独重写过 C 的措辞（摘要、实习条目、论文 note、技能…），
    # A/B 当时没跟上，于是集合必然不同。**当天 A/B 已按 C 同步完毕**，所以现在两边也应当对齐，
    # 差异只该剩下 ONLY_IN 里写明理由的那几条。对 C 仍不判失败，只报数量——
    # C 的事实覆盖面另由第 2 条地标清单（论文/荣誉/经历/关键数字）兜底。
    # 判断标准变了：以前「有差异」是常态，现在「有差异」是信号——多半是新改的措辞没同步。
    ref = "A"
    for k in "BC":
        extra = fs[k] - fs[ref] - ONLY_IN.get(k, set())
        miss  = fs[ref] - fs[k] - ONLY_IN.get(ref, set())
        if k == "C":
            if extra or miss:
                # 差异不多时逐条列出来：只剩一两条的时候，数量本身说明不了问题，
                # 得看见那一条是什么才知道该不该动。
                #
                # **已知且有意的一条**（2026-09-30，本人拍板）：页眉标语里
                # A/B 是「智能体强化学习 / 长程 Agent 训练」，C 保持
                # 「智能体强化学习 / Harness Agent 训练」。三份里那条「长程/Harness」的差异
                # 就是这一处，**不是漏改，别顺手去同步**。当时问过本人：人才计划版保留原话术。
                # 之所以不塞进 ONLY_IN 抹掉：那等于把差异藏起来；留在这条提示里，
                # 下次真出现别的漏改时，还能靠「项数变了」看出来。
                print(f"  C 与 {ref} 措辞不同：C 独有 {len(extra)} 项、{ref} 独有 {len(miss)} 项"
                      f"（不判失败；事实覆盖见第 2 条）")
                for x in sorted(extra)[:5]:
                    print(f"      C 有而 {ref} 没有：{x[:58]}")
                for x in sorted(miss)[:5]:
                    print(f"      {ref} 有而 C 没有：{x[:58]}")
            else:
                print(f"  C 与 {ref} 一致（{len(fs[k])} 项）")
            continue
        if not extra and not miss:
            print(f"  {k} 与 {ref} 一致（{len(fs[k])} 项）")
            continue
        bad += 1
        print(f"  {k} 与 {ref} 不一致：")
        for x in sorted(miss):
            print(f"    {k} 缺少（{ref} 有）：{x}")
        for x in sorted(extra):
            print(f"    {k} 多出（{ref} 没有）：{x}")

    print("== 2. 地标事实（论文/荣誉/经历/关键数字） ==")
    for fact in LANDMARKS:
        variants = (fact,) if isinstance(fact, str) else fact
        hit = {}
        for k in "ABC":
            found = [v for v in variants if norm(v) in text[k]]
            hit[k] = found[0] if found else None
        absent = [k for k in "ABC" if hit[k] is None]
        if not absent:
            if len({hit[k] for k in "ABC"}) == 1:
                f = norm(hit["A"])
                cnt = {k: text[k].count(f) for k in "ABC"}
                tag = f"×{cnt['A']}" if len(set(cnt.values())) == 1 else \
                      f"次数 A{cnt['A']}/B{cnt['B']}/C{cnt['C']}"
                print(f"  ok   {tag:>14}  {f[:64]}")
            else:   # 各版用词不同：把三份各自的写法都显示出来
                print(f"  ok   {'A/B/C 用词不同':>12}  " +
                      " ｜ ".join(f"{k}:{norm(hit[k])[:28]}" for k in "ABC"))
        else:
            bad += 1
            print(f"  !!   只在 {''.join(k for k in 'ABC' if hit[k]) or '（无）'}  —— "
                  f"{norm(variants[0])[:64]}")

    if args.check_html:
        print("== 3. 产物 HTML 没漏渲染事实 ==")
        for k in "ABC":
            p = OUT_HTML / HTML[k]
            if not p.exists():
                print(f"  !!  {k}: 缺产物 {p.name}（先跑 build.py）")
                bad += 1
                continue
            hay = html_haystack(p)
            skip = UNRENDERED.get(k, set())
            misses = sorted(f for f in fs[k] - skip if f not in hay)
            stale  = sorted(f for f in skip if f in hay)       # 豁免已失效
            if not misses and not stale:
                print(f"  ok   {k} {LABEL[k]}：{len(fs[k]) - len(skip)} 项数据事实全部可见"
                      f"（{len(skip)} 项按设计不渲染）")
            if misses:
                bad += 1
                print(f"  !!   {k} {LABEL[k]}：{len(misses)} 项在数据里但页面上看不到")
                for f in misses[:20]:
                    print(f"        - {f[:72]}")
            if stale:
                bad += 1
                print(f"  !!   {k} {LABEL[k]}：UNRENDERED 里有 {len(stale)} 项其实渲染了，"
                      f"该从豁免清单里删掉")
                for f in stale:
                    print(f"        - {f[:72]}")

    print(("校验通过。" if not bad else f"共 {bad} 处问题。"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())