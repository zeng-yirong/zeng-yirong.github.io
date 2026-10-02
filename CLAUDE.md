# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个学术主页（Hugo 静态站），中英双语，托管在 GitHub Pages。
输出目录是 Hugo 默认的 `public/`，**但不提交进仓库** —— 2026-10-01 起
Pages 由 GitHub Actions 部署，仓库里不再保存构建产物。

## Common Commands

```bash
# 本地预览 —— 必须带 -M
#   publishDir = "public"，不加 -M 的话 dev server 会把带 localhost:1313 和 livereload
#   的开发构建直接写进 public/，覆盖掉本地那份产物，核对时容易看走眼。
hugo server -M

# 本地构建（产出 public/，已被 gitignore）—— 带 --minify 是为了和 CI 一致
#   workflow 里跑的就是 hugo --minify；本地用同一条命令，出问题才复现得出来。
#   线上不由这条命令上线，见下面「上线路径」。
hugo --minify

# 从 CV 的数据重新生成主页内容（改了 CV/build/data/ 之后跑）
python scripts/sync-homepage.py
```

### 上线路径

**push main → GitHub Actions 自动构建并部署。** 没有别的步骤。

`.github/workflows/hugo.yml` 在 CI 里跑 `hugo --minify`，把 `./public` 作为 artifact
交给 `actions/deploy-pages`。**仓库里不保存构建产物**（`public/` 已 gitignore），所以：

> ⚠️ **手改 `public/` 对线上没有任何影响。** 要改样式或文案，必须改源文件 ——
> `layouts/`、`assets/`、`data/`、`config.toml`。这条对以前「改产物再提交」的习惯
> 是个反转，见记忆 cv-edits-in-output-html。

历史：2026-10-01 之前 Pages 是「Deploy from a branch / docs」模式，线上服务的直接
就是仓库里提交的 `docs/`，所以当时必须本地构建后提交。那天用户把 source 切成了
「GitHub Actions」，`docs/` 随之出库（提交 `a579927`）。
输出目录原先一直叫 `docs/`（branch 模式的遗留），2026-10-03 改回 Hugo 默认的 `public/`
—— 「docs」这名字和「文档」的直觉相反，留着每次都要解释一遍。

几个坑：

- **workflow 钉的 Hugo 版本必须与本地一致**（`hugo version` 可查）。它原先写的
  0.74.3 是 2020 年的版本，跑不动现在的模板/配置 —— 在 branch 模式下这没造成问题
  （线上走的是提交的 `docs/`），但切到 Actions 后会直接构建失败。
- `hugo server` **一定要加 `-M`**（`--renderToMemory`），否则 dev server 的产物
  （带 `http://localhost:1313` 和 livereload `<script>`）会覆盖本地 `public/`。
  本地 `public/` 不上线，但覆盖了会让你本地核对时看走眼。
- **怎么确认 Actions 真在部署**：workflow 的 badge 是纯 SVG，可以直接 curl ——
  `curl -s https://github.com/zeng-yirong/zeng-yirong.github.io/actions/workflows/hugo.yml/badge.svg`
  返回 `<title>… - passing</title>` 就说明默认分支上最近一次运行成功（切到 Actions
  之前 `actions/deploy-pages` 必然失败，badge 会是 failing）。
  **Actions 页面本身是 JS 渲染的，抓 HTML 拿不到任何运行数据，别走那条路。**

## Architecture

### 目录

```
config.toml      配置：段落开关、颜色、以及短到不值得外置的几行内容（双语两棵树）
data/            **内容产物**，由 scripts/sync-homepage.py 从 CV 生成，不要手改
  publications.yaml      论文 15 条（标题/作者/venue/链接两语言共用，徽章分语言）
  software.yaml          开源与数据集 4 条
  en/experience.yaml     华为实习（英文）
  zh/experience.yaml     华为实习（中文）
scripts/         仓库自己的小工具
  sync-homepage.py       生成 data/ 的脚本（规则与覆盖表都在文件顶部）
  homepage-en.yaml       英文译文（手工维护）—— CV 数据全是中文，译文推不出来
layouts/         本站的模板（原 themes/hugo-devresume-theme/layouts，已提升到根）
assets/scss/     SCSS 源
static/          favicon.ico、assets/images/{me,avatar}.png
i18n/            en.yaml / zh.yaml，12 个键，两语言各一套全套键
public/          本地构建产物，**已 gitignore**（线上由 CI 构建，见「上线路径」）
CV/              简历构建系统（独立的一套，见 CV/build/README.md）
```

### 主题已本地化（没有 themes/ 目录）

原来用 `themes/hugo-devresume-theme/`，2026-10-01 提升到了仓库根，`config.toml` 里不再有
`theme =`。原因：从「更新前端现代版本」那次改版起这份主题就再没跟过上游，`theme.toml`
指向的 cowboysmall-tools 那份已经合不回来；继续挂在 `themes/` 下只会让所有站点文件白白深一层，
而且 `i18n/` 会出现「项目级 vs 主题级」两层、每次都要解释谁覆盖谁。

`LICENSE.md` 是原主题的 MIT 协议，提升时一并移到了根目录。

### 双语

```toml
defaultContentLanguage = "en"                 # 英文是默认语言，站点根 / 就是英文页
defaultContentLanguageInSubdir = false        # 英文不放进 /en/，中文在 /zh/
```

**两棵 params 树都写全**（`[languages.en.params]` / `[languages.zh.params]`），根上不留
`[params]`。不写成「根上放共用项、语言里只覆盖文字」，是因为 Hugo 对**数组**的合并语义
在版本间不一致（覆盖还是追加说不准）—— 一旦变成追加，英文那 15 篇论文就会出现在中文页上。

`public/en/` 是 Hugo 为「默认语言不进子目录」自动生成的跳转页（跳回 `/`），删了会重新生成，不用管。

### 内容的分工

| 数据 | 在哪 | 谁维护 |
|---|---|---|
| 论文、开源、华为实习 | `data/` | **脚本生成**，改 `CV/build/data/A-general.yaml` 后重跑 |
| 英文译文 | `scripts/homepage-en.yaml` | 手工（译文无法从 CV 推出） |
| 段落开关、颜色、头像、联系方式、教育、兴趣 | `config.toml` | 手工 |

`scripts/sync-homepage.py` 顶部集中放着「CV 字段 → 主页写法」的排版规则（日期连字符、
标题补句点、作者行 `（共一）` 归一、venue 的 Findings/Main 拆分、7 篇的完整作者名单覆盖等），
以及一张显式的覆盖表。**组名/条数对不上时脚本直接报错**，不会静默漏内容。

CV 的三份数据里只有 **A**（`A-general.yaml`）与主页同形（有 `internship`/`publications`/
`opensource` 块）；C 是 timeline 结构，字段对不上。三份的事实由 `CV/build/validate.py` 保证一致。

### Partial 契约（改模板前先看）

- `layouts/index.html` 主栏顺序写死：**experience → projects → information → software**；
  侧栏（`sidebar.html`）：interests → education → internships → awards → skills → hobbies → languages。
- 段落是否渲染由 `config.toml` 的 `enable` 控制；**数据来源**在 partial 里：
  `experience.html` / `information.html` / `software.html` 读 `.Site.Data`，其余读 `.Site.Params`。
- `experience.html` 只支持「一段 details + 一个扁平 `<ul>`」，所以实习的三个分组是用一条
  **只有粗体组名**的条目当小标题（`**组名**`），`markdownify` 渲染成 `<strong>`。
- Hugo 的 data 是「先目录后文件名」：`data/en/experience.yaml` → `.Site.Data.en.experience`，
  所以是 `index (index .Site.Data .Site.Language.Lang) "experience"` 两层。
- `information.html` 渲染 `title` / `authors` / `badge.<lang>`，有 `href` 就用 `<a class="paper-venue">`，
  没有就退化成 `<span class="paper-venue">`（**两者样式相同，外观上区分不出可不可点**）。
- 语言切换器在 `header.html` 顶部，自己占一行。**不能用 `"/" | relLangURL`** ——
  那个函数永远按*当前*语言拼前缀，在 `range .Site.Languages` 里对每种语言都会拼出当前语言的地址；
  必须从 `.Translations` 取目标语言那一页的 `.Permalink`。
- `head.html` 的 favicon 必须走 `relURL`（写成相对的 `favicon.ico` 时 `/zh/` 页会去找
  `/zh/favicon.ico` 而 404）；`og:url` / `twitter:url` 用 `.Permalink`，否则中文页指回英文页。

### 视觉约定

- 主色 `primaryColor` / `textPrimaryColor` 在 `config.toml` 的两个语言下各写一份，值相同。
- 不显示的部件**以 HTML 注释保留**在模板里，不删除（以后可能还要用）。
- 改版式的请求常常是「只动被点名的那一项」—— 别顺手扩大范围。