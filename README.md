# 曾屹荣 · 个人主页

中英双语的学术主页，Hugo 静态站，托管在 GitHub Pages。

**线上地址：<https://zeng-yirong.github.io/>**（中文，默认）· <https://zeng-yirong.github.io/en/>（English）

---

## 环境要求

| 用途 | 需要什么 |
|---|---|
| **改主页 / 本地预览** | [Hugo **0.157.0 extended**](https://github.com/gohugoio/hugo/releases/tag/v0.157.0) |
| 从简历数据重新生成主页内容 | Python 3 + `pip install pyyaml` |
| 构建简历 PDF（`CV/`，可选） | Python 3 + `pip install pyyaml jinja2 playwright pypdf`，再 `python -m playwright install chromium` |

> ⚠️ **Hugo 版本必须与 CI 一致**。`.github/workflows/hugo.yml` 里钉的就是 `0.157.0`，
> 版本不同会导致本地看到的和线上部署出来的不是一回事。用 `hugo version` 核对。
>
> Windows 安装：`winget install Hugo.Hugo.Extended --version 0.157.0`。
> 装完要**重开终端** PATH 才生效。

---

## 快速开始

```bash
# 本地预览 —— -M 不能省
hugo server -M
# 打开 http://localhost:1313/

# 本地构建（产出 public/，已被 gitignore）
hugo --minify
```

**`-M` 是 `--renderToMemory`**，不加的话 dev server 会把带 `localhost:1313` 和
livereload 脚本的开发版产物写进 `public/`，覆盖掉你本地那份用于核对的构建结果。

---

## 目录结构

```
config.toml      站点配置：段落开关、颜色、语言设置，以及短到不值得外置的内容
                 （头像、联系方式、教育、研究方向、爱好、社交链接）
data/            长内容，**由脚本生成，不要手改**（见下节）
  publications.yaml       论文（两语言共用；status 区分已录用/在投）
  software.yaml           开源项目与数据集
  en/interests.yaml       研究方向（英文）
  zh/interests.yaml       研究方向（中文）
  en/experience.yaml      实习经历（英文）
  zh/experience.yaml      实习经历（中文）
layouts/         页面模板
  index.html              主页骨架，段落顺序在这里写死
  partials/               各段落（header / summary / information / experience / ...）
  404.html                双语 404 页
assets/scss/     SCSS 源（devresume.scss + bootstrap/）
i18n/            界面固定文案（en.yaml / zh.yaml，两份键集必须一致）
static/          favicon.ico、头像 assets/images/me.png
  cv/                    三个版本的简历 HTML（CV 系统的产物，发布到 /cv/）
scripts/         仓库自己的小工具
  sync-homepage.py        从简历数据生成 data/ 的脚本
  homepage-en.yaml        英文译文（手工维护）
CV/              简历构建系统（独立的一套，见 CV/build/README.md）
public/          本地构建产物，已 gitignore
```

---

## 内容怎么改

**这是最容易踩坑的地方：主页的长内容不在 `config.toml` 里，而是从简历数据生成出来的。**

| 你要改的东西 | 改哪里 |
|---|---|
| 论文、开源项目、研究方向、实习经历 | `CV/build/data/A-general.yaml`，然后重跑生成脚本（见下） |
| 上面这些的**英文**表述 | `scripts/homepage-en.yaml`（译文推不出来，只能手工写） |
| 段落开关、颜色、头像、联系方式、教育、研究方向、爱好、社交 | `config.toml` |

### 重新生成主页内容

```bash
python scripts/sync-homepage.py
```

脚本从 `CV/build/data/A-general.yaml` 读事实，从 `scripts/homepage-en.yaml` 读英文译文，
写出 `data/` 下的六个文件。

- **不要手改 `data/` 下的文件** —— 它们每次都会被整个覆盖。
- ⚠️ **`data/` 是提交进仓库的，而 CI 不跑这个脚本。** 忘了重跑、或者跑了却忘了
  `git add` 新文件，Hugo 不会报错（取不到的键静默为空），线上会安静地少一整段。
  改完务必 `python scripts/sync-homepage.py && git status --short` 确认干净。
- 排版规则（日期格式、标题补句点、作者行归一、venue 拆分等）集中在
  `scripts/sync-homepage.py` 文件顶部，以及一张显式的覆盖表。
- **组名/条数对不上时脚本会直接报错**，不会静默漏内容。

---

## 双语

```toml
defaultContentLanguage = "zh"              # 中文是默认语言，站点根 / 就是中文页
defaultContentLanguageInSubdir = false     # 中文不放进 /zh/，英文在 /en/
```

所以：**中文在 `/`，英文在 `/en/`**。`/zh/` 是 Hugo 自动生成的跳转页（老链接不会死），
删了会重新生成，不用管。

> ⚠️ 改 `defaultContentLanguage` 会**同时改变 URL 布局**，不只是换默认显示。
> 改之前先确认没有对外发过的链接依赖 `/` 是某种语言。

`config.toml` 里**两棵 params 树都写全**（`[languages.en.params]` 与 `[languages.zh.params]`），
根上不留 `[params]`。这是因为 Hugo 对**数组**的合并语义在版本间不一致（覆盖还是追加说不准）——
一旦变成追加，中文页上就会冒出英文的论文。两棵写全 = 不依赖任何合并行为。

**加 i18n 键时，`i18n/en.yaml` 和 `i18n/zh.yaml` 必须一起加**：项目级 i18n 会整体覆盖主题自带的那份，
缺的键不会回退，会直接在页面上印出键名。

---

## 上线

**push 到 `main` → GitHub Actions 自动构建并部署。没有别的步骤。**

```bash
git add -A && git commit -m "..." && git push
```

CI 跑 `hugo --minify`，把 `public/` 作为 artifact 交给 `actions/deploy-pages`。

> ⚠️ **仓库里不保存构建产物。** `public/` 已 gitignore，手改它对线上没有任何影响。
> 要改样式或文案，必须改源文件 —— `layouts/`、`assets/`、`data/`、`config.toml`。

**怎么确认部署成功**：workflow badge 是纯 SVG，可以直接 curl：

```bash
curl -s https://github.com/zeng-yirong/zeng-yirong.github.io/actions/workflows/hugo.yml/badge.svg
```

返回 `<title>… - passing</title>` 就说明默认分支上最近一次运行成功。
（Actions 页面本身是 JS 渲染的，抓 HTML 拿不到任何运行数据，别走那条路。）

---

## 简历构建系统（`CV/`）

`CV/` 是一套**独立于主页**的系统：`resume.yaml` 数据 + Jinja2 模板 → HTML + A4 PDF，
三个版本（通用版 A / 研究院版 B / 人才计划版 C）各有各的数据文件和模板。

```bash
cd CV/build
python build.py            # 三份全出（HTML + PDF）
python build.py --style C  # 只出某一版
python build.py --no-pdf   # 只出 HTML，快速预览
python validate.py         # 校验三份数据承载的事实是否一致
```

产物**是刻意提交进仓库的**，分两处：HTML 落在 `static/cv/`（由站点发布，
主页头部就链接着它们，线上在 <https://zeng-yirong.github.io/cv/>），
PDF 留在 `CV/build/output/pdf/`（供从仓库直接下载）。

⚠️ **`static/cv/` 里是产物，而 CI 不跑 `build.py`** —— 改了数据却忘了重跑并提交，
线上就是旧简历，Hugo 不会报任何错。防线是 `python validate.py --check-html`。

详细说明见 **[CV/build/README.md](CV/build/README.md)**。

> 主页的 `data/` 就来自这里的 `A-general.yaml`（只有 A 版与主页同形）。
> 改完简历数据要重跑 `python scripts/sync-homepage.py`，主页才会跟着变。

---

## 几个容易踩的坑

- **`hugo server` 一定要加 `-M`** —— 否则开发版产物会覆盖本地 `public/`，核对时看走眼。
- **`data/` 是产物，不是源** —— 改内容去改 `CV/build/data/`，再跑生成脚本。
- **改 `publishDir` 要连 workflow 一起改** —— CI 里 `path:` 必须与 `config.toml` 的
  `publishDir` 指向同一个目录，分开改会让 artifact 为空、部署失败。
- **`disableKinds` 必须写在 `[languages]` 之前** —— TOML 里裸键只属于第一张表头之前的根表，
  写进去会变成 `languages.disableKinds`，Hugo 连警告都不会给。
- **GitHub Pages 只用发布根目录的那一份 `404.html`** —— `/en/` 下的 404 也拿根那份，
  所以根那份必须自带两个语言的入口。

更多架构层面的约定（partial 契约、视觉约定、改版式时的注意事项）见 [CLAUDE.md](CLAUDE.md)。
