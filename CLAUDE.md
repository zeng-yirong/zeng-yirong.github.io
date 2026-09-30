# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个学术主页（Hugo 静态站），中英双语，托管在 GitHub Pages。
输出目录是 `docs/`（不是默认的 `public/`），并且 **`docs/` 是提交进仓库的**。

## Common Commands

```bash
# 本地预览 —— 必须带 -M
#   publishDir = "docs"，不加 -M 的话 dev server 会把带 localhost:1313 和 livereload
#   的开发构建直接写进 docs/，覆盖掉待提交的产物，然后被一起 commit 上线。
hugo server -M

# 构建（产出 docs/）—— 必须带 --minify
#   线上那份 docs/ 就是 minify 过的；漏了这个参数会让整个 docs/ 全量重写一遍。
hugo --minify

# 从 CV 的数据重新生成主页内容（改了 CV/build/data/ 之后跑）
python scripts/sync-homepage.py
```

### 上线路径

**本地 `hugo --minify` → 提交 `docs/` → push main。** GitHub Pages 服务的是仓库里的
`docs/` 目录。只改模板/配置而不重建、不提交，线上不会变。

几个坑：

- `hugo server` **一定要加 `-M`**（`--renderToMemory`），否则污染 `docs/`（见上）。
- 构建产物提交前先扫一遍：`grep -rl -e localhost -e livereload docs/` 应该没有输出。
- `.github/workflows/hugo.yml` 钉的 Hugo 版本必须与本地一致（`hugo version` 可查）。
  它原先写的 0.74.3 是 2020 年的版本，跑不动现在的模板/配置 —— 那个 Action 从未产出线上页面。
  目前 Pages 的 source 仍可能是「分支 /docs」，**别以为推代码就会自动部署**。

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
docs/            构建产物，**提交进仓库**，Pages 直接服务这里
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

`docs/en/` 是 Hugo 为「默认语言不进子目录」自动生成的跳转页（跳回 `/`），删了会重新生成，不用管。

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