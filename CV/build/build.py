#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一条命令：resume.yaml（唯一数据源） -> 各样式 HTML + PDF
用法：
  python3 build.py                          # 全部样式 × default profile
  python3 build.py --style B                # 只出样式B
  python3 build.py --profile talent         # 人才计划版
  python3 build.py --all-profiles           # 三个版本(default/talent/institute)全量生成
  python3 build.py --no-pdf                 # 只出HTML不压PDF
输出：CV/build/output/{html,pdf}/resume-{style}-{profile}.(html|pdf)
"""
import argparse, copy, re, sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent          # CV/build
DATA = ROOT / "resume.yaml"
OUT_HTML = ROOT / "output" / "html"
OUT_PDF = ROOT / "output" / "pdf"

STYLES = {
    "A": "style-A-sidebar.html.j2",
    "B": "style-B-minimal.html.j2",
    "C": "style-C-tech-timeline.html.j2",
}
DEFAULT_ORDER = ["summary", "highlights_bar", "education", "internship",
                 "research_focus", "publications", "opensource", "awards", "projects", "skills"]

def md_bold(s: str) -> str:
    """极简行内标记：**xx** -> <em>xx</em>（构建期处理，模板零逻辑）"""
    return re.sub(r"\*\*(.+?)\*\*", r"<em>\1</em>", s or "")

def load_data(profile: str) -> dict:
    d = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    ov = copy.deepcopy(d.get("profiles", {}).get(profile, {}).get("overrides", {})) if profile != "default" else {}
    d["_ov"] = ov
    # 照片转 base64 内联：输出文件自包含（PDF/HTML 不依赖相对路径）
    ph = (DATA.parent.parent / d["basics"]["photo"].replace("../", "")).resolve()
    if not ph.exists():
        ph = DATA.parent.parent / "personal-photo.jpg"
    if ph.exists():
        import base64
        mime = "image/png" if ph.suffix.lower() == ".png" else "image/jpeg"
        d["basics"]["photo_b64"] = f"data:{mime};base64," + base64.b64encode(ph.read_bytes()).decode()
    else:
        d["basics"]["photo_b64"] = d["basics"]["photo"]
    # 预处理：把 internship 条目里的 **bold** 转成 <em>，模板直接 safe 输出
    for g in d["internship"]["groups"]:
        for it in g["items"]:
            it["html"] = md_bold(it["text"])
    return d

def render(env: Environment, style: str, d: dict, profile: str) -> str:
    tpl = env.get_template(STYLES[style])
    return tpl.render(d=d, ov=d["_ov"], profile_name=profile,
                      md=lambda t: __import__("jinja2").Markup(md_bold(t)))

def to_pdf(html_path: Path, pdf_path: Path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        # 版式留白由模板 CSS 控制，PDF 边距归零保证整页背景完整
        page.pdf(path=str(pdf_path), format="A4", print_background=True, scale=0.95,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=list(STYLES) + ["ABC"], default="ABC")
    ap.add_argument("--profile", default="default")
    ap.add_argument("--all-profiles", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()

    OUT_HTML.mkdir(parents=True, exist_ok=True)
    OUT_PDF.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"], default_for_string=False),
                      trim_blocks=True, lstrip_blocks=True)
    env.policies["template_class"] = env.policies.get("template_class")  # keep default

    styles = list(STYLES) if args.style == "ABC" else [args.style]
    profiles = ["default", "talent", "institute"] if args.all_profiles else [args.profile]

    made = []
    for st in styles:
        for pf in profiles:
            d = load_data(pf)
            html = render(env, st, d, pf)
            hp = OUT_HTML / f"resume-{st}-{pf}.html"
            hp.write_text(html, encoding="utf-8")
            made.append(str(hp))
            if not args.no_pdf:
                pp = OUT_PDF / f"resume-{st}-{pf}.pdf"
                to_pdf(hp, pp)
                made.append(str(pp))
    print("Generated %d files:" % len(made))
    for m in made:
        print("  ", m)

if __name__ == "__main__":
    sys.exit(main())
