#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 CV 的数据生成到主页的 data/ 下。

    在仓库根目录跑：  python scripts/sync-homepage.py

数据源（唯一事实来源）：
    CV/build/data/A-general.yaml   —— 三份 CV 数据里只有 A 是「主页同形」的
                                      （有 internship / publications / opensource 这些块；
                                       C 是 timeline 结构，字段对不上）。
                                      三份的事实由 CV/build/validate.py 保证一致。
    scripts/homepage-en.yaml       —— 英文译文（CV 全是中文，译文推不出来，只能手工维护）。

产物（**全部是自动生成的，不要手改**）：
    data/publications.yaml         论文 15 条，标题/作者/venue/链接两语言共用，
                                   徽章措辞按语言各一份（badge.en / badge.zh）；
                                   status（published/pending）决定「已录用/在投」的样式
    data/software.yaml             开源 4 条，name / desc / authors 按语言各一份
    data/zh/interests.yaml         研究方向（中文，全部从 CV 生成）
    data/en/interests.yaml         研究方向（英文，结构从 CV、文案来自 homepage-en.yaml）
    data/zh/experience.yaml        华为实习（中文，全部从 CV 生成）
    data/en/experience.yaml        华为实习（英文，结构从 CV、文案来自 homepage-en.yaml）

模板侧只改了「range 的来源」：从 .Site.Params.xxx.list 改成上面的 data 文件。
段落的开关（enable）仍在 config.toml 里，没动。
"""

import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
# stderr 也要设：报错信息是中文，Windows 控制台默认 GBK，不设的话
# 调用方（以及重定向到文件时）会拿到乱码，甚至解码失败。
sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CV_DATA = os.path.join(ROOT, "CV", "build", "data", "A-general.yaml")
EN_PROSE = os.path.join(ROOT, "scripts", "homepage-en.yaml")
DATA_DIR = os.path.join(ROOT, "data")

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：pip install pyyaml")

GENERATED_BY = "python scripts/sync-homepage.py"


# ============================================================
# 排版规则：把 CV 的字段拼成主页上显示的样子
#
# CV 的数据是给简历 PDF 用的，写法和主页有几处对不上。这些差异**显式列在这里**，
# 不藏在生成逻辑里；改 CV 之后如果哪条对不上了，脚本会报错而不是悄悄生成错的东西。
# ============================================================

# CV 的 venue 与主页的写法差异：
#   EMNLP 的 Findings/Main 在 CV 里并进了 venue 字段，主页拆成「会议 | 分轨」
#   NAACL 的 Main 在 CV 里根本没写，但主页一直显示着 —— 补上，别丢信息
VENUE_TRACK = {
    "EMNLP 2025 Findings": ("EMNLP 2025", "Findings"),
    "EMNLP 2025 Main": ("EMNLP 2025", "Main"),
    "NAACL 2025": ("NAACL 2025", "Main"),
}

# CV 的 tier 字段（A/B/P/Q1）→ 徽章上的档位写法
TIER_LABEL = {"A": "CCF-A", "B": "CCF-B", "Q1": "SCI-Q1", "P": "CCF-A"}

# 一作 / 共一 的说法
ROLE_LABEL = {
    "first": ("First Author", "一作"),
    "co": ("Co-First Author", "共一"),
}

# CV 的日期用 en dash（2024.09 – 2026.09），主页用的是连字符。
# 统一成连字符，与主页教育那两行的写法保持一致。
def norm_date(s):
    return s.replace("–", "-").replace("—", "-")


# 主页的论文标题一律带结尾句点，CV 的一律不带。
def norm_title(s):
    s = s.strip()
    return s if s.endswith(".") else s + "."


# CV 的作者行写「Yufei Liu*, Yirong Zeng*（共一）, et al.」（全角括号），
# 主页一直显示的是 ASCII 的 "(co-first)"。归一到主页的写法，别因为改数据源而改版式。
def norm_authors(s):
    s = s.replace("（共一）", "(co-first)")
    return re.sub(r"(?<!\s)\(co-first\)", " (co-first)", s)


def authors_of(pub, prose):
    """完整名单优先用 scripts/homepage-en.yaml 的 authors 覆盖（CV 是缩写式，会丢信息）。"""
    title = pub["title"]
    for prefix, full in prose.get("authors", {}).items():
        if title.startswith(prefix):
            return full
    return norm_authors(pub["authors"])


# 主页的实习职位抬头比 CV 的 role 长一截（CV 只写「AI算法工程师」，身份放 lead 里）。
# CV 里那条注释明确说「不要并排成两个身份」，主页当初把身份合进了标题，就按主页的写法定死在这里。
ZH_EXPERIENCE_TITLE = "AI 算法工程师（研究型实习生）"

# 第 4 条开源（Demo）不在 CV 的 opensource 里 —— CV 的 projects 里是「惊堂木」，
# 主页用的却是另一套措辞和另一个链接。整个条目写死在这里，并从 opensource 的生成里排除。
SOFTWARE_DEMO = {
    "name": "Misinformation Detection",
    "desc": {
        "en": "Real-time Rumor Identification & Evidence Tracing",
        "zh": "实时谣言识别与证据溯源",
    },
    "authors": {"en": "Yirong Zeng, Juyi Dai, Shen You", "zh": "Yirong Zeng, Juyi Dai, Shen You"},
    "meta": "Demo System",
    "href": "https://huggingface.co/spaces/You-shen/React",
}


# CV 的 org 是「华为（北京）小艺 · 基础算法开发部」，侧栏只有 ~240px 宽，
# 放不下整串。取第一个「·」之前的部分（EN 的 prose company 同样含「·」，规则通用）。
# 断言而不是静默截断：哪天 CV 把「·」去掉了，这里要报错让人来改规则，
# 而不是悄悄把整串塞进侧栏、把排版撑坏。
def norm_org_short(s):
    if "·" not in s:
        sys.exit("组织名 %r 里没有「·」，侧栏取短名的规则（norm_org_short）需要更新" % s)
    return s.split("·")[0].strip()


# ============================================================
# YAML 输出：手写序列化，为的是控制排版和注释
# ============================================================

def q(s):
    """双引号 YAML 字符串。"""
    s = str(s)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").strip()
    return '"%s"' % s


def header(title, note_lines=()):
    out = ["# " + "=" * 58,
           "# %s" % title,
           "#",
           "# 自动生成，请勿手改 —— 改 %s 里的源数据后跑" % os.path.relpath(CV_DATA, ROOT).replace("\\", "/"),
           "#     python scripts/sync-homepage.py",
           "# 本文件会被整个覆盖。"]
    for line in note_lines:
        out.append("# %s" % line if line else "#")
    out.append("# " + "=" * 58)
    return "\n".join(out) + "\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  写入 %s" % os.path.relpath(path, ROOT).replace("\\", "/"))


# ============================================================
# 论文
# ============================================================

def badge_of(pub, status):
    """拼徽章。status: published / pending。返回 (en, zh)。"""
    venue = pub["venue"]
    base, track = VENUE_TRACK.get(venue, (venue, None))
    tier = TIER_LABEL.get(pub["tier"])
    if tier is None:
        sys.exit("论文 %r 的 tier=%r 没有对应的档位写法" % (pub["title"][:40], pub["tier"]))

    if status == "published":
        role = ROLE_LABEL["co" if pub.get("co") else "first"]
        en = "%s | %s%s, %s" % (base, ("%s, " % track) if track else "", tier, role[0])
        zh = "%s ｜ %s%s，%s" % (base, ("%s，" % track) if track else "", tier, role[1])
    else:
        # 在投：CV 的 tier 一律是 P，档位沿用该会议本该投中的档（TIER_LABEL 里 P 映射到 CCF-A）
        en = "%s | Under Review, %s" % (base, tier)
        zh = "%s ｜ 在投，%s" % (base, tier)
    return en, zh


def gen_publications(cv, prose):
    pubs = cv["publications"]
    lines = [header("论文（已发表在前，顺序与 CV 一致）",
                    ["标题 / 作者 / venue 两个语言页共用（学术惯例不译标题），",
                     "徽章措辞按语言各一份：badge.en / badge.zh。",
                     "",
                     "status 取 CV 的 published / pending —— 模板用它区分「已录用」与",
                     "「在投」的徽章样式（实心 vs 描边），不再靠徽章文案里那两个字。",
                     "",
                     "三处对 CV 的规整（都在 sync-homepage.py 顶上写着）：",
                     "  标题补结尾句点（CV 不带、主页带）",
                     "  作者行的「（共一）」写成 ASCII 的 (co-first)",
                     "  7 篇的完整作者名单来自 scripts/homepage-en.yaml —— CV 的 authors 是缩写式，",
                     "  直接用会把名单截短"])]

    matched = set()
    n = 0
    for status, key in (("published", "published"), ("pending", "pending")):
        for pub in pubs.get(key, []):
            title = norm_title(pub["title"])
            authors = authors_of(pub, prose)
            for prefix in prose.get("authors", {}):
                if pub["title"].startswith(prefix):
                    matched.add(prefix)
            en, zh = badge_of(pub, status)
            lines.append("")
            lines.append("- title: %s" % q(title))
            lines.append("  authors: %s" % q(authors))
            lines.append("  status: %s" % q(status))
            lines.append("  badge:")
            lines.append("    en: %s" % q(en))
            lines.append("    zh: %s" % q(zh))
            if pub.get("url"):
                lines.append("  href: %s" % q(pub["url"]))
            n += 1

    unused = [k for k in prose.get("authors", {}) if k not in matched]
    if unused:
        sys.exit("scripts/homepage-en.yaml 的 authors 里这些开头没匹配到任何论文：%s" % "、".join(unused))

    write(os.path.join(DATA_DIR, "publications.yaml"), "\n".join(lines) + "\n")
    return n


# ============================================================
# 开源 / 数据集
# ============================================================

def gen_software(cv, prose):
    items = []
    for o in cv["opensource"]:
        name = o["name"]
        try:
            en_desc = prose["software"][name]["desc"]
        except KeyError:
            sys.exit("scripts/homepage-en.yaml 的 software 里没有 %r 这一条" % name)
        items.append({
            "name": name,
            "desc": {"en": en_desc, "zh": o["desc"]},
            # 作者行：开源这几条都是「本人主导」的缩写式
            "authors": {"en": "Yirong Zeng, et al.", "zh": "曾屹荣 等"},
            # CV 的 metric 是「⭐ 33」这种，主页跟一个平台名
            "meta": o["metric"] + (" · GitHub" if "github.com" in o.get("link", "") else ""),
            "href": o["link"],
        })

    items.append(SOFTWARE_DEMO)

    lines = [header("开源项目与数据集",
                    ["name / desc / authors 按语言各一份，meta 与 href 两语言共用。",
                     "前 3 条从 CV 的 opensource 生成；第 4 条（Demo）不在 CV 里，",
                     "写死在 scripts/sync-homepage.py 的 SOFTWARE_DEMO。",
                     "",
                     "字段是拆开的：早先 title 里塞的是「名称 - 描述」、name 里塞的是",
                     "作者行，模板只能靠字符串切分来分行，容易出错。"])]
    for it in items:
        lines.append("")
        lines.append("- name: %s" % q(it["name"]))
        lines.append("  desc:")
        lines.append("    en: %s" % q(it["desc"]["en"]))
        lines.append("    zh: %s" % q(it["desc"]["zh"]))
        lines.append("  authors:")
        lines.append("    en: %s" % q(it["authors"]["en"]))
        lines.append("    zh: %s" % q(it["authors"]["zh"]))
        lines.append("  meta: %s" % q(it["meta"]))
        lines.append("  href: %s" % q(it["href"]))
    write(os.path.join(DATA_DIR, "software.yaml"), "\n".join(lines) + "\n")
    return len(items)


# ============================================================
# 实习经历
# ============================================================

def gen_experience(cv, prose):
    job = cv["internship"]
    zh_groups = job["groups"]
    en_groups = prose["experience"]["groups"]

    # 组名对不上就直接报错：宁可不生成，也不要静默漏掉一组成果
    missing = [g["title"] for g in zh_groups if g["title"] not in en_groups]
    if missing:
        sys.exit("scripts/homepage-en.yaml 的 experience.groups 缺少这些组：%s" % "、".join(missing))
    unused = [k for k in en_groups if k not in {g["title"] for g in zh_groups}]
    if unused:
        sys.exit("scripts/homepage-en.yaml 里这些组名在 CV 中不存在：%s" % "、".join(unused))

    for g in zh_groups:
        en = en_groups[g["title"]]
        if len(en["items"]) != len(g["items"]):
            sys.exit("组 %r 的条数对不上：CV %d 条，译文 %d 条"
                     % (g["title"], len(g["items"]), len(en["items"])))

    dates = norm_date(job["time"])
    out = {}
    for lang in ("zh", "en"):
        lines = [header("华为实习（主栏 Experience）",
                        ["%s 侧%s。" % ("中文" if lang == "zh" else "英文",
                                      "全部从 CV 生成" if lang == "zh"
                                      else "结构从 CV 生成、文案来自 scripts/homepage-en.yaml"),
                         "",
                         "三个分组在 CV 里是 internship.groups，主页模板只支持「一段 details +",
                         "一个扁平 <ul>」，所以每组用一条**只有粗体组名**的条目当小标题"
                         "（模板会 markdownify 成 <em>）。"])]
        company = prose["experience"]["company"] if lang == "en" else job["org"]
        lines.append("")
        lines.append("- title: %s" % q(prose["experience"]["title"] if lang == "en" else ZH_EXPERIENCE_TITLE))
        lines.append("  company: %s" % q(company))
        lines.append("  dates: %s" % q(dates))
        # 侧栏「实习经历」那一条用，拆成两行（机构粗体 + 日期灰色），和「教育背景」
        # 那段的排版一致。侧栏只有 ~240px 宽，org 全称（「华为（北京）小艺 · 基础算法
        # 开发部」）放不下，所以取短名。读这份数据而不是让 config.toml 再抄一份 ——
        # 日期就不会和主栏漂移。
        lines.append("  sidebar_org: %s" % q(norm_org_short(company)))
        lines.append("  sidebar_dates: %s" % q(dates))
        lines.append("  details: %s" % q(prose["experience"]["details"] if lang == "en" else job["lead"]))
        lines.append("  items:")
        for g in zh_groups:
            en = en_groups[g["title"]]
            head = en["title"] if lang == "en" else g["title"]
            lines.append("    - details: %s" % q("**%s**" % head))
            body = en["items"] if lang == "en" else g["items"]
            for it in body:
                lines.append("    - details: %s" % q(it))
        out[lang] = "\n".join(lines) + "\n"

    write(os.path.join(DATA_DIR, "zh", "experience.yaml"), out["zh"])
    write(os.path.join(DATA_DIR, "en", "experience.yaml"), out["en"])


# ============================================================
# 研究方向（主栏 interests）
# ============================================================

def gen_interests(cv, prose):
    zh_groups = cv["research_focus"]
    en_groups = prose["research_focus"]

    # 与 gen_experience 同构的两种校验：组名缺 / 多，都直接报错而不是静默丢内容
    missing = [g["name"] for g in zh_groups if g["name"] not in en_groups]
    if missing:
        sys.exit("scripts/homepage-en.yaml 的 research_focus 缺少这些组：%s" % "、".join(missing))
    unused = [k for k in en_groups if k not in {g["name"] for g in zh_groups}]
    if unused:
        sys.exit("scripts/homepage-en.yaml 里这些组名在 CV research_focus 中不存在：%s" % "、".join(unused))

    for g in zh_groups:
        en = en_groups[g["name"]]
        if len(en["bullets"]) != len(g["bullets"]):
            sys.exit("研究方向组 %r 的条数对不上：CV %d 条，译文 %d 条"
                     % (g["name"], len(g["bullets"]), len(en["bullets"])))
        # CV 的 time 里有中文「至今」，英文整串人工给 —— 这里校验起始日期没写错，
        # 防的是「CV 改了日期、homepage-en.yaml 忘了跟着改」。
        start = norm_date(g["time"]).split()[0]
        if not norm_date(en["time"]).startswith(start):
            sys.exit("研究方向组 %r 的英文 time=%r 与 CV 起始日期 %r 对不上，译文可能过期"
                     % (g["name"], en["time"], start))

    out = {}
    for lang in ("zh", "en"):
        lines = [header("研究方向（主栏 interests）",
                        ["%s 侧%s。" % ("中文" if lang == "zh" else "英文",
                                      "全部从 CV 生成" if lang == "zh"
                                      else "文案与 time 都来自 scripts/homepage-en.yaml"),
                         "",
                         "为什么英文连 time 都要整串给：CV 里写的是「2024.09 – 至今」，",
                         "带中文「至今」，norm_date() 只换破折号、推不出英文。",
                         "",
                         "模板用原生 <details open> 渲染，一组一条；bullets 是纯文本，",
                         "不过 markdownify（CV 里这几条本来就没有 markdown）。"])]
        for g in zh_groups:
            en = en_groups[g["name"]]
            lines.append("")
            lines.append("- name: %s" % q(en["name"] if lang == "en" else g["name"]))
            lines.append("  time: %s" % q(norm_date(en["time"]) if lang == "en" else norm_date(g["time"])))
            lines.append("  bullets:")
            for b in (en["bullets"] if lang == "en" else g["bullets"]):
                lines.append("    - %s" % q(b))
        out[lang] = "\n".join(lines) + "\n"

    write(os.path.join(DATA_DIR, "zh", "interests.yaml"), out["zh"])
    write(os.path.join(DATA_DIR, "en", "interests.yaml"), out["en"])
    return len(zh_groups)


# ============================================================

def main():
    for p in (CV_DATA, EN_PROSE):
        if not os.path.exists(p):
            sys.exit("找不到 %s" % p)
    cv = yaml.safe_load(open(CV_DATA, encoding="utf-8"))
    prose = yaml.safe_load(open(EN_PROSE, encoding="utf-8"))

    print("源：%s" % os.path.relpath(CV_DATA, ROOT).replace("\\", "/"))
    n_pub = gen_publications(cv, prose)
    n_soft = gen_software(cv, prose)
    n_int = gen_interests(cv, prose)
    gen_experience(cv, prose)
    print("完成：论文 %d 条、开源 %d 条、研究方向 %d 组、实习 %d 组。"
          % (n_pub, n_soft, n_int, len(cv["internship"]["groups"])))
    print("本地预览：hugo server -M；上线：push main（CI 构建，不用提交产物）")


if __name__ == "__main__":
    main()