# 简历构建系统（内容与版式分离）

## 目录结构
```
CV/build/
├── resume.yaml                 # ★ 唯一数据源：论文列表、经历条目全部结构化在这里
├── build.py                    # 一条命令生成 HTML + PDF（Jinja2 + Playwright-Chromium）
├── templates/                  # 3 个版式模板（只管排版，不含任何内容）
│   ├── style-A-sidebar.html.j2        # A 深蓝侧栏现代风（含照片）
│   ├── style-B-minimal.html.j2        # B 极简单栏学术风（LaTeX 感，打印最佳）
│   └── style-C-tech-timeline.html.j2  # C 渐变科技时间轴风（含照片）
└── output/
    ├── html/resume-{A|B|C}-{default|talent|institute}.html
    └── pdf /resume-{A|B|C}-{default|talent|institute}.pdf   # A4 ×4 页
```

## 日常用法
```bash
cd CV/build
python3 build.py --all-profiles            # 全量：3样式 × 3版本 = 9 份 PDF
python3 build.py --style B --profile talent # 只出「人才计划版·样式B」
python3 build.py --no-pdf                   # 快速预览只出 HTML
```

## 多版本机制（profiles）
`resume.yaml` 末尾 `profiles:` 定义各版本的差异（段落顺序、头部徽章），内容主体共用一份：
- `default`   —— 通用版
- `talent`    —— 人才计划版：荣誉前置 + 科协专项/华为人才计划/国奖徽章
- `institute` —— 研究院版：研究方向+论文前置，突出学术主线

新增版本 = 在 profiles 下加一段 overrides，重跑一条命令即可。

## 高亮语法
数据里 `**文本**` 构建时自动转为强调色（无需改模板）。

## 依赖
`pip install pyyaml jinja2 playwright && python3 -m playwright install chromium`
