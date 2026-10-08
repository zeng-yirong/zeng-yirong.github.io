#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一条命令：data/<版本>.yaml（各自独立的数据源） -> 该版本的 HTML + PDF

一版一数据；模板通常一版一份，**D 是唯一的例外**（与 C 共用一份，见 VARIANTS 里的注释）。
各份数据不共享任何字段：

  版本         数据文件                模板                            输出
  A 通用版     data/A-general.yaml     style-A-sidebar.html.j2        resume-A-general.*
  B 研究院版   data/B-institute.yaml   style-B-minimal.html.j2        resume-B-institute.*
  C 人才计划版 data/C-talent.yaml      style-C-tech-timeline.html.j2  resume-C-talent.*
  D 华为专供版 data/D-huawei.yaml      （同上，与 C 共用）             resume-D-huawei.*

用法：
  python build.py                # 四份全出（HTML + PDF）
  python build.py --style C      # 只出人才计划版（字母 = 数据与模板名）
  python build.py --no-pdf       # 只出 HTML，快速预览

改完数据后另跑 python validate.py 校验各份文件承载的事实是否一致。
"""
import argparse
import base64
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT     = Path(__file__).resolve().parent          # CV/build
CV_DIR   = ROOT.parent                              # CV
DATA_DIR = ROOT / "data"
TPL_DIR  = ROOT / "templates"
# HTML 产物直接写进站点的 static/cv/ —— 主页头部要链接这三份简历，
# 而 Hugo 只发布 static/ 下的东西。放在这里就没有第二份会漂移的副本。
# （ROOT 是 CV/build，仓库根是它的上两级。）
OUT_HTML = ROOT.parent.parent / "static" / "cv"
# 不进站的版本（VARIANTS 里 publish: False，当前只有 D 华为专供版）的 HTML 落点：
# 与 PDF 并列放在 build/output/ 下，站点的 static/cv/ 里不会出现它。
OUT_HTML_LOCAL = ROOT / "output" / "html"
OUT_PDF  = ROOT / "output" / "pdf"
PHOTO    = CV_DIR / "personal-photo.jpg"            # 固定常量：与数据文件所在目录解耦

VARIANTS = {
    "A": {"basename": "A-general",   "data": "A-general.yaml",   "label": "通用版",
          "tpl": "style-A-sidebar.html.j2"},
    "B": {"basename": "B-institute", "data": "B-institute.yaml", "label": "研究院版",
          "tpl": "style-B-minimal.html.j2"},
    "C": {"basename": "C-talent",    "data": "C-talent.yaml",    "label": "人才计划版",
          "tpl": "style-C-tech-timeline.html.j2"},
    # D = C 的派生版（2026-10-08 本人要求）。两处与别版不同，都写在这里而不是散在代码里：
    #   publish: False —— **不上线**：HTML 与 PDF 都出到 build/output/，不写进站点的
    #     static/cv/，主页头部那行链接也不加它（本人选的「只出文件，不上线」）。
    #     想把 D 也发布到 /cv/，删掉这一行即可（产物会改写到 static/cv/）。
    #   tpl 与 C 同一个 —— 这是「一版一模板」的明示例外：D 与 C 只差数据（顺序、简介、
    #     实习时间），照抄一份 411 行的模板只会让以后每改一次 C 的版式都要同步两遍。
    "D": {"basename": "D-huawei",    "data": "D-huawei.yaml",    "label": "华为专供版",
          "tpl": "style-C-tech-timeline.html.j2", "publish": False},
}

# 校验用：每版期望的顶层键，以及各版允许出现在顺序表里的段落名
REQUIRED = {
    "A": ["sidebar", "main_sections", "summary", "education", "internship",
          "research_focus", "publications", "opensource", "awards", "projects"],
    "B": ["header", "sections", "summary", "education", "internship",
          "research_focus", "publications", "opensource", "awards", "projects", "skills"],
    "C": ["hero", "kpis", "order", "timeline", "summary", "publications", "awards", "skills"],
    # D 与 C 同结构（同模板），所以这三张表都照抄 C 的那一行。
    "D": ["hero", "kpis", "order", "timeline", "summary", "publications", "awards", "skills"],
}
BLOCKS = {                       # 顺序表里可写的「整块」段落名
    "A": {"summary", "education", "internship", "research_focus", "publications",
          "opensource", "awards", "projects"},
    "B": {"summary", "highlights", "education", "internship", "research_focus",
          "publications", "opensource", "awards", "projects", "skills"},
    "C": {"summary", "publications", "awards", "skills"},
    "D": {"summary", "publications", "awards", "skills"},
}
ORDER_KEY = {"A": "main_sections", "B": "sections", "C": "order", "D": "order"}

# C 版数据里各结构的合法键。为什么值得单独挡一道：拼错的键（把 pgbreak 写成 pagebreak）
# 在模板里只会取到 Undefined——不报错、不渲染、断页静默消失，肉眼很难发现。
# 加新键时改这里一处，别在模板里加「如果写错就…」的兜底。
C_KEYS = {
    "rail":  {"rail", "icon", "title", "note", "pgbreak"},
    "pair":  {"pair", "ratio"},
    "pubs":  {"published", "pending", "pgbreak"},
    # 整块段落（summary / publications / awards / skills）也能带 pgbreak——
    # 写成 {block: "publications", pgbreak: true}。2026-10-08 加：D 版的论文段正好落在
    # 第 2 页页首，不给它 .pgbreak 就没有那 20px 页顶留白（正文会贴到纸边 2pt，见 README）。
    # 光写成字符串 `- publications` 是带不了断页的（模板只从 mapping 行读 pgbreak）。
    "block": {"block", "pgbreak"},
}


def md_bold(s: str) -> str:
    """极简行内标记：**xx** -> <em>xx</em>（构建期处理，模板零逻辑）"""
    return re.sub(r"\*\*(.+?)\*\*", r"<em>\1</em>", s or "")


def photo_uri() -> str:
    """照片内联为 base64，输出文件自包含。缺失则返回空串（模板会跳过 <img>）。"""
    if not PHOTO.exists():
        print(f"warning: 缺少照片 {PHOTO}，产物中不显示头像", file=sys.stderr)
        return ""
    mime = "image/png" if PHOTO.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(PHOTO.read_bytes()).decode()


def load_data(path: Path) -> dict:
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        raise SystemExit(f"{path} 不是一个 YAML 映射")
    d["photo_uri"] = photo_uri()
    return d


def check(style: str, d: dict, path: Path) -> list:
    """轻量自检：拼错段落名或漏接数据要报错，而不是静默少渲染一段。"""
    errs = []
    for k in REQUIRED[style]:
        if k not in d:
            errs.append(f"缺少顶层键 {k!r}")

    order = d.get(ORDER_KEY[style]) or []
    for row in order:
        # 顺序表元素允许「一行两栏」：写成列表 = 这两个段落并排。
        # 栏内元素的写法与单栏时完全一样（段落名 / 带 rail 的字典）。
        # 也可写成 {pair: [左, 右], ratio: [a, b]}——并排且带逐行栏宽比（配平两栏高度）。
        if isinstance(row, list):
            if len(row) != 2:
                errs.append(f"并排行 {row!r} 有 {len(row)} 栏，目前只支持 2 栏")
            entries = row
        elif isinstance(row, dict) and "pair" in row:
            entries = row["pair"]
            if not isinstance(entries, list) or len(entries) != 2:
                errs.append(f"pair 行 {row!r} 必须给 2 栏，目前只支持 2 栏")
                entries = entries if isinstance(entries, list) else []
            ratio = row.get("ratio")
            if ratio is None:
                errs.append(f"pair 行 {row!r} 缺少 ratio（两栏宽度比，如 [1, 1]）")
            elif not isinstance(ratio, list) or len(ratio) != 2 or not all(
                    isinstance(x, (int, float)) and x > 0 for x in ratio):
                errs.append(f"pair 行的 ratio {ratio!r} 必须是两个正数，如 [0.8, 1.2]")
        else:
            entries = [row]
        for blk in entries:
            # 顺序表元素有两种写法：段落名字符串 / 带元信息的字典（B 用 key，C 用 rail）
            if isinstance(blk, str):
                name = blk
            elif isinstance(blk, dict) and "rail" in blk:
                types = d.get("timeline") or []
                have = {e.get("type") for e in types}
                for t in blk["rail"]:
                    if t not in have:
                        errs.append(f"rail {t!r} 在 timeline 里没有任何条目（可选：{sorted(have)}）")
                continue
            elif isinstance(blk, dict) and "key" in blk:
                name = blk["key"]
            elif isinstance(blk, dict) and "block" in blk:
                name = blk["block"]
            else:
                errs.append(f"顺序表元素 {blk!r} 既不是段落名，也不是带 key/rail 的字典")
                continue

            if name not in BLOCKS[style]:
                errs.append(f"段落名 {name!r} 不是 {style} 版的合法段落，"
                            f"可选：{sorted(BLOCKS[style])}")
            elif name not in d:
                errs.append(f"顺序表引用了 {name!r}，但数据里没有这个段落")

    if style in ("C", "D"):              # timeline 条目必须有槽位，否则会静默消失
        rails = set()
        for row in order:
            if isinstance(row, dict) and "pair" in row:
                row = row["pair"]
            for blk in (row if isinstance(row, list) else [row]):
                if isinstance(blk, dict) and "rail" in blk:
                    rails.update(blk["rail"])
        for e in d.get("timeline") or []:
            t = e.get("type")
            if not t:
                errs.append(f"timeline 条目缺少 type：{e.get('title')!r}")
            elif t not in rails and not e.get("unrendered"):
                # `unrendered: true` = 这条**故意**不渲染（D 版撤掉「研究方向」段就是用它）。
                # 没有这个标记却又没有 rail 选中，才是「漏渲染」——那才会报错。
                errs.append(f"timeline 条目 type={t!r}（{e.get('title')!r}）没有任何 rail 选中，会被漏渲染"
                            "（确属故意不渲染就给它加 unrendered: true）")

        # 拼错的键 = 静默失效（见 C_KEYS 的注释），逐层点名
        def keys_of(row, kind):
            allowed = C_KEYS[kind]
            # 报错只列键名，不打印整行——pubs 那行的数据有十几篇论文，铺开会淹掉报错本身
            for k in row:
                if k not in allowed:
                    errs.append(f"{kind} 行里有不认识的键 {k!r}"
                                f"（该行现有：{sorted(row)}；可用：{sorted(allowed)}）")
            if "pgbreak" in row and not isinstance(row["pgbreak"], bool):
                errs.append(f"{kind} 行的 pgbreak 必须是 true/false，现在是 "
                            f"{row['pgbreak']!r}——写成字符串不会报错但会静默失效"
                            f"（该行现有：{sorted(row)}）")

        for row in order:
            if isinstance(row, dict):
                kind = "block" if "block" in row else ("pair" if "pair" in row else "rail")
                keys_of(row, kind)
        pub = d.get("publications")
        if isinstance(pub, dict):
            keys_of(pub, "pubs")

        # 数字横条的开关（kpis 那一节的注释写了用途）。两类静默失效都要挡：
        # 写成字符串 "false" 会被当成真→横条凭空出现；为 true 但 kpis 为空→产物里
        # 连注释都没有，将来想启用时无从下手。
        if "kpis_comment_only" in d and not isinstance(d["kpis_comment_only"], bool):
            errs.append(f"kpis_comment_only 必须是 true/false，现在是 "
                        f"{d['kpis_comment_only']!r}——写成字符串会被当成真，横条会凭空出现")
        if d.get("kpis_comment_only") and not d.get("kpis"):
            errs.append("kpis_comment_only 为 true，但 kpis 是空的：产物里不会留下任何注释，"
                        "将来想启用这条横条时无从下手（要么把 kpis 填上，要么删掉这个开关）")

    # 页码开关（见 PAGE_FOOTER 那段注释）。两类静默问题都要挡：
    # 写 "false" 会被当成真、页码凭空出现；而 @page 下边距为 0 的版式底部没有页脚带子，
    # 页脚会被画到正文上——那是个非致命但很难看的静默故障。
    if "page_numbers" in d and not isinstance(d["page_numbers"], bool):
        errs.append(f"page_numbers 必须是 true/false，现在是 {d['page_numbers']!r}"
                    "——写成字符串会被当成真，页码会凭空出现")
    if d.get("page_numbers"):
        rule = FOOTER_BAND.get(style)
        if rule is None:
            errs.append(f"{style} 版模板的 @page 下边距是 0（留白靠元素自身 padding），"
                        "页面底部没有页脚带子；打开 page_numbers 前要先让出底部留白，"
                        "并重新量分页（那会真的挤掉正文高度）")
        else:
            tpl_text = (TPL_DIR / VARIANTS[style]["tpl"]).read_text(encoding="utf-8")
            if rule not in tpl_text:
                errs.append(f"{style} 版开着 page_numbers，但模板里的 @page 已经不是 "
                            f"{rule!r}——页脚带子没了，页码会压到正文上。"
                            "改了模板的 @page 就要同步 FOOTER_BAND 这条登记")

    # 纵向留白的三个数据旋钮（C/D 模板的 CSS 变量，见模板 :root 那段注释）。
    # 都默认取 C 的老值，逐版覆盖：page_top_pad=续页页顶留白(20)、
    # pubs_gap=论文列表盒首那道缝(20)、subhead_gap=「在投论文」小标题上方(30)。
    # 写成字符串会拼出 "40pxpx" 这种非法值——CSS 静默忽略 → 该留白归零、版式塌掉，
    # 页数也跟着变。所以这里逐键挡一道，别让它静默生效。
    for key in ("page_top_pad", "pubs_gap", "subhead_gap"):
        if key in d:
            v = d[key]
            if isinstance(v, bool) or not isinstance(v, int):
                errs.append(f"{key} 必须是整数（像素值），现在是 {v!r}"
                            "——写成字符串会在 CSS 里拼出 '40pxpx'，那条留白会静默归零")
    return errs


def render(env: Environment, style: str, d: dict) -> str:
    tpl = env.get_template(VARIANTS[style]["tpl"])
    return tpl.render(d=d, md=lambda t: Markup(md_bold(t)))


# 页码（数据里写 page_numbers: true 才加）。**只能由 Chromium 的 footer 画，不能靠 CSS**：
# Chromium 至今不支持 @page 的页边内容（@bottom-center 之类），HTML 里没有 page 计数器。
# 关键点：footer 是画在**页边距那条带子里**的，不是内容区——所以它不吃正文高度。
# B 的 `@page{margin:14mm 0}` 本来就在页面底部留了 14mm 空白（正文最多写到 803pt、
# 页高 843pt），页脚落在那条带子里（实测 y≈819pt），页数与正文位置都不动（2026-09-30 实测）。
# 反过来，若某版把 @page 下边距设成 0（A/C 就是 `margin:0`，留白靠元素自身的 padding），
# 就没有这条带子——要给它加页码得先让出底部留白，那会真的挤掉正文、必须重新量分页。
# 页眉则必须显式压掉：display_header_footer=True 会把**页眉和页脚一起**打开，
# 不给 header_template 的话 Chromium 会画它自带的默认页眉（日期 + 网页标题 + 网址），
# 于是每页顶上多出一行「2026/9/30 00:16 曾屹荣 · 简历 — 样式B：…」（实测踩过）。
# 传一个「有内容但看不见」的 div，比传空串可靠——空串会被当成没给、又退回默认页眉。
PAGE_HEADER = '<div style="height:0"></div>'
PAGE_FOOTER = ('<div style="width:100%;font-size:8pt;color:#5b6472;text-align:center;'
               'font-family:Arial,Helvetica,sans-serif">'
               '第 <span class="pageNumber"></span> 页 / 共 <span class="totalPages"></span> 页</div>')

# 页脚带子的登记表：**这个版式的模板里 @page 那条规则的原文**。
# 有登记 = 该版 @page 留了非 0 的下边距，页码画得进那条带子、不吃正文高度；
# 没登记 = 下边距为 0，开 page_numbers 会静默把页脚压到正文上，check() 直接挡掉。
# 值必须与模板逐字相符，check() 会去模板里找——这样「有人把 @page 改回 margin:0」
# 或「模板改了这里忘了改」都会当场报错，而不是等印出来才发现页码叠在字上。
# A 没登记：A 的 @page 也是 margin:0，且 A 本人没要页码。
FOOTER_BAND = {
    "B": "@page{size:A4;margin:14mm 0}",
    "C": "@page{size:A4;margin:0 0 10mm}",
    "D": "@page{size:A4;margin:0 0 10mm}",   # 与 C 共用模板，登记值也必须与 C 相同
}


def to_pdf(html_path: Path, pdf_path: Path, page_numbers: bool = False):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("需要 playwright：python -m pip install playwright "
                         "&& python -m playwright install chromium")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        # 版式留白由模板 CSS 控制，PDF 边距归零保证整页背景完整。
        # 页脚那条带子用的就是 CSS 的 @page 下边距，所以这里不必（也不该）再传边距：
        # 传了等于把 CSS 的 14mm 覆盖成别的值，正文区会跟着变、分页全乱。
        opts = {}
        if page_numbers:
            opts = {"display_header_footer": True,
                    "header_template": PAGE_HEADER, "footer_template": PAGE_FOOTER}
        page.pdf(path=str(pdf_path), format="A4", print_background=True, scale=0.95,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}, **opts)
        browser.close()


def page_count(pdf_path: Path) -> int:
    """粗略页数（数 /Type /Page，排除 /Pages）。精确值用 pypdf。"""
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf_path.read_bytes()))


def main():
    # Windows 控制台默认 GBK，中文报错会变乱码
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=list(VARIANTS), default=None,
                    help="只生成一个版本（默认三份全出）")
    ap.add_argument("--no-pdf", action="store_true", help="只出 HTML，不压 PDF")
    args = ap.parse_args()

    OUT_HTML.mkdir(parents=True, exist_ok=True)
    OUT_PDF.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(TPL_DIR),
                      autoescape=select_autoescape(["html"], default_for_string=False),
                      trim_blocks=True, lstrip_blocks=True)

    for st in ([args.style] if args.style else list(VARIANTS)):
        v = VARIANTS[st]
        path = DATA_DIR / v["data"]
        d = load_data(path)
        errs = check(st, d, path)
        if errs:
            raise SystemExit(f"{path.name} 校验失败：\n  - " + "\n  - ".join(errs))

        out_html = OUT_HTML if v.get("publish", True) else OUT_HTML_LOCAL
        out_html.mkdir(parents=True, exist_ok=True)
        hp = out_html / f"resume-{v['basename']}.html"
        hp.write_text(render(env, st, d), encoding="utf-8")
        line = f"  {v['label']:<7} {hp.name}"
        if not v.get("publish", True):
            line += "（不上线：产物在 build/output/，不在站点里）"
        if not args.no_pdf:
            pp = OUT_PDF / f"resume-{v['basename']}.pdf"
            to_pdf(hp, pp, page_numbers=bool(d.get("page_numbers")))
            line += f"  + {pp.name}  (~{page_count(pp)} 页)"
        print(line)


if __name__ == "__main__":
    sys.exit(main())