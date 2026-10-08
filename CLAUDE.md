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
  publications.yaml      论文 15 条（标题/作者/venue/链接两语言共用，徽章分语言；
                         status 分 published/pending，决定徽章是实心还是描边）
  software.yaml          开源与数据集 4 条（name/desc/authors 分语言）
  en/interests.yaml      研究方向（英文）—— 分文件而非 en:/zh: 子键，因为每句都是译文
  zh/interests.yaml      研究方向（中文）
  en/experience.yaml     华为实习（英文）
  zh/experience.yaml     华为实习（中文）
scripts/         仓库自己的小工具
  sync-homepage.py       生成 data/ 的脚本（规则与覆盖表都在文件顶部）
  homepage-en.yaml       英文译文（手工维护）—— CV 数据全是中文，译文推不出来
layouts/         本站的模板（原 themes/hugo-devresume-theme/layouts，已提升到根）
assets/scss/     SCSS 源
static/          favicon.ico、assets/images/me.png（头像）
  cv/                    ★ 三个版本的简历 HTML（A/B/C，发布到 /cv/）
                          —— D 华为专供版**不上线**，HTML 在 CV/build/output/html/
i18n/            en.yaml / zh.yaml，12 个键，两语言各一套全套键
public/          本地构建产物，**已 gitignore**（线上由 CI 构建，见「上线路径」）
CV/              简历构建系统（独立的一套，见 CV/build/README.md）
```

⚠️ **`static/cv/` 里是提交进仓库的产物**（由 `CV/build/build.py` 生成，2026-10-03 从
`CV/build/output/html/` 搬过来，为的是让主页头部能链接它们 —— Hugo 只发布 `static/` 下的东西）。
**2026-10-08 起 `output/html/` 又有人住了**：D 华为专供版按本人要求「只出文件、不上线」，
HTML 出在那里（`VARIANTS["D"]["publish"] = False`）。**不上线 ≠ 保密**：仓库是公开的。
CI 只跑 `hugo --minify`、**不跑 build.py**：改了 CV 数据却忘了重跑并提交，线上就是旧简历，
**Hugo 不会报任何错**。唯一防线是 `python CV/build/validate.py --check-html`。

### 主题已本地化（没有 themes/ 目录）

原来用 `themes/hugo-devresume-theme/`，2026-10-01 提升到了仓库根，`config.toml` 里不再有
`theme =`。原因：从「更新前端现代版本」那次改版起这份主题就再没跟过上游，`theme.toml`
指向的 cowboysmall-tools 那份已经合不回来；继续挂在 `themes/` 下只会让所有站点文件白白深一层，
而且 `i18n/` 会出现「项目级 vs 主题级」两层、每次都要解释谁覆盖谁。

`LICENSE.md` 是原主题的 MIT 协议，提升时一并移到了根目录。

### 双语

```toml
defaultContentLanguage = "zh"                 # 中文是默认语言，站点根 / 就是中文页
defaultContentLanguageInSubdir = false        # 中文不放进 /zh/，英文在 /en/
```

**两棵 params 树都写全**（`[languages.en.params]` / `[languages.zh.params]`），根上不留
`[params]`。不写成「根上放共用项、语言里只覆盖文字」，是因为 Hugo 对**数组**的合并语义
在版本间不一致（覆盖还是追加说不准）—— 一旦变成追加，英文那 15 篇论文就会出现在中文页上。

`public/zh/` 是 Hugo 为「默认语言不进子目录」自动生成的跳转页（跳回 `/`），删了会重新生成，不用管。
它顺带兜住了一个坑：2026-10-03 之前中文在 `/zh/`，改默认语言后那个地址会失效 —— 正因为 Hugo
生成这份跳转页，老书签才没死。反过来说，**默认语言的旧子目录永远会是跳转页**，别把它当成
「中文页还在 /zh/」的证据。

⚠️ 改 `defaultContentLanguage` 会**同时改变 URL 布局**，不只是换默认显示。2026-10-03 从 en 改成 zh
时，`/` 从英文页变成中文页、英文挪到 `/en/`。改之前先确认没有对外发过的链接依赖 `/` 是英文。

### 输出 kind 与 404（两处反直觉，改前先看）

**`disableKinds = ["taxonomy", "term", "rss"]` 必须写在 `[languages]` 之前。**
TOML 里裸键只属于第一张表头之前的根表，写到 `[languages]` 底下会变成
`languages.disableKinds`，而且 **Hugo 连警告都不会发**，只是静默不生效。

为什么关：本站没有 `content/`，但 Hugo 默认仍生成 tags/categories 的 kind。它们没有
对应的 `index.html`（本站没有 list 模板），于是 GitHub Pages 把那份 `index.xml` 直接
当目录页返回 —— 修之前线上 `/categories/` `/tags/` 是 **200 + `application/xml`**，
访客看到的是裸 RSS，而 sitemap 每语言只列 3 个 URL、其中 2 个正是这些伪页面。
关掉后它们变成真 404。`sitemap` 不列入（要保留），全站模板也没有任何地方引用 RSS。

**404 页只有发布根那一份会被 GitHub Pages 当回退。** `public/zh/404.html` 由 Hugo
照常生成，但只作为普通静态文件被直接访问到（返回 200），**永远不参与 404 回退**。
所以 `layouts/404.html` 必须自带两个语言的入口，也就**不能用 `header.html` 那个语言
切换器** —— 它依赖 `.Translations`，而 404 页没有译文，循环会空转。改用
`.Site.Home.AllTranslations`（注意 `.Sites` 自 v0.156 起已弃用）。

顺带一条：0 字节的模板 **不产出任何文件**。原先 `layouts/404.html` 是空的，所以线上
一份 404.html 都没有，走的是 GitHub 默认英文页 —— 排查「模板写了但线上没变化」时先看
文件是不是空的。

### 内容的分工

| 数据 | 在哪 | 谁维护 |
|---|---|---|
| 论文、开源、研究方向、华为实习 | `data/` | **脚本生成**，改 `CV/build/data/A-general.yaml` 后重跑 |
| 英文译文 | `scripts/homepage-en.yaml` | 手工（译文无法从 CV 推出） |
| 段落开关、颜色、头像、联系方式与三个 CV 链接、教育、社交、两段早期实习 | `config.toml` | 手工 |

`summary.text`（个人简介）**允许 markdown**（模板走 `| markdownify`，`summary.html`），
目前用它给实验室挂了链接。⚠️ **别在字符串里加空行** —— 空行会让 markdownify 返回 `<p>`，
嵌进外层 `<p class="mb-0">` 是非法嵌套，浏览器会把外层 `<p>` 拆掉（静默的排版炸弹）。
另外 Bootstrap 4 的 `a` 默认没有下划线，正文里的链接会「不像链接」，
所以 `.resume-intro a` 单独补了下划线处理。

`contact.cv` 是头部那一行三个简历链接。⚠️ 模板里必须用 **`relURL`**，不能用 `relLangURL` ——
后者在 `/en/` 页会拼出 `/en/cv/…`（404），和 `head.html` 里 favicon 那条是同一类坑。

⚠️ **`data/` 是提交进仓库的，而 CI 不跑 `sync-homepage.py`。** 忘了重跑、或者跑了却忘了
`git add` 新文件，Hugo 不会报错（`index` 取不到的键静默为空），线上会安静地少一整段。
改完务必 `python scripts/sync-homepage.py && git status --short` 确认干净。

`scripts/sync-homepage.py` 顶部集中放着「CV 字段 → 主页写法」的排版规则（日期连字符、
标题补句点、作者行 `（共一）` 归一、venue 的 Findings/Main 拆分、7 篇的完整作者名单覆盖等），
以及一张显式的覆盖表。**组名/条数对不上时脚本直接报错**，不会静默漏内容。

CV 的四份数据里只有 **A**（`A-general.yaml`）与主页同形（有 `internship`/`publications`/
`opensource` 块）；C 是 timeline 结构、D 是 C 的派生版（2026-10-08 加的华为专供版），
字段都对不上。四份的事实由 `CV/build/validate.py` 保证一致——D 与 C 之间有 15/4 项
**有意**差异（华为版简介 + 实习时间「至今」），校验器只报告、不判失败。

### Partial 契约（改模板前先看）

- `layouts/index.html` 主栏顺序写死：**interests → information → experience → projects → software**；
  侧栏（`sidebar.html`）：education → internships → awards → skills → hobbies → languages。
  - 2026-10-03 调整：`interests`（研究方向）从侧栏移到主栏顶部，位置在**头像+简介之后、论文之前**；
    `experience` 从原先打头退到**论文之后**。理由：学术主页以论文为重心，且实习已简化成一段总述。
  - 简化只发生在模板层：`experience.html` 里的 9 条要点用 `{{ if false }}` 挂着，数据仍完整保留在
    `data/<lang>/experience.yaml`。要恢复就把那个 `if false` 换成 `if .items` —— 别去手改 yaml，它下次生成会被覆盖。
- 段落是否渲染由 `config.toml` 的 `enable` 控制；**数据来源**在 partial 里：
  `experience.html` / `information.html` / `software.html` / `interests.html` 读 `.Site.Data`，
  其余读 `.Site.Params`。
- `experience.html` 只支持「一段 details + 一个扁平 `<ul>`」，所以实习的三个分组是用一条
  **只有粗体组名**的条目当小标题（`**组名**`），`markdownify` 渲染成 `<strong>`。
  注意那 9 条要点现在被 `{{ if false }}` 挂起来了（见上一条的「简化只发生在模板层」）。
- Hugo 的 data 是「先目录后文件名」：`data/en/experience.yaml` → `.Site.Data.en.experience`，
  所以是 `index (index .Site.Data .Site.Language.Lang) "experience"` 两层。
- `information.html` 把两个维度分成**两条互不干扰的视觉通道**：
  `status`（published/pending）→ 徽章的填充方式（实心 vs 描边）；
  有没有 `href` → **标题**带不带下划线。早先徽章兼任链接、且有无链接样式完全相同，
  结果「录用了没」和「能不能点」糊在一起 —— 别再合并回去。
- **段落折叠**：每个带标题的段落都是一个 `<details class="section-fold" open>`，
  默认展开、可收起，无 JS。分组级的折叠（研究方向的两组）再嵌一层。
  - 🚫 **`<h1>`–`<h6>` 永远不放进 `<summary>`。** `<summary>` 的隐含角色是 button，
    而 ARIA 里 **button 的子元素是 presentational** —— Firefox / WebKit 与 JAWS
    因此**不把 summary 里的 h3 当标题暴露**（只有 Chrome 和 NVDA 会）。放进去
    并没有真的保住标题导航，只是把 h3 留给了爬虫。
  - 标题语义一律放在 `<details>` **外面**：分段级折叠的可见标题只能落在 summary 里时，
    就在 `<details>` 前补一个 `<h3 class="sr-only">`（`.sr-only` 是 Bootstrap 自带的，
    不用新加类）；已经在外面的（研究方向的分组 —— section 级 `<h3>` 在 details 之前），
    summary 里直接用 `<span>`。
  - 代价是标题文字在 a11y 树里出现两次（heading + button 名），这是这个模式的固有代价，
    ARIA APG 的 disclosure 模式也这么做。
  - ⚠️ 折叠相关的交互样式（`flex` / `cursor` / `list-style` / `:focus-visible`）
    写在 **`.section-fold > summary`** 上，**不要并进 `.resume-section-heading`** ——
    `404.html` 的 `<h3>` 也挂那个类。
  - 别加 `name` 属性（那是手风琴互斥语义，这里要各自独立）。
- `interests.html` 用**原生 `<details open>`** 渲染研究方向的分组，无 JS。
  Bootstrap 4 只给 `summary` 加了 `display:list-item`，原生三角一定会显示，
  要显式关掉再自己画（`.interest-summary` 那段，和段落折叠共用一套规则）。
- `internships.html` 里华为那条读 `data/<lang>/experience.yaml` 的 `sidebar_org` /
  `sidebar_dates`，**不往 `config.toml` 再抄一份** —— 抄了的话 CV 改日期时侧栏会和主栏
  并存两个不同的日期，没有任何机制拦得住。config 里只留主页独有、CV 里没有的两段。
- 语言切换器在 `header.html` 顶部，自己占一行。**不能用 `"/" | relLangURL`** ——
  那个函数永远按*当前*语言拼前缀，在 `range .Site.Languages` 里对每种语言都会拼出当前语言的地址；
  必须从 `.Translations` 取目标语言那一页的 `.Permalink`。
- `head.html` 的 favicon 必须走 `relURL`（写成相对的 `favicon.ico` 时 `/en/` 页会去找
  `/en/favicon.ico` 而 404）；`og:url` / `twitter:url` 用 `.Permalink`，否则英文页指回中文页。
- `head.html` **不再加载任何 webfont**（2026-10-03 删掉）。原先那个 Google Fonts 的
  Roboto 从来没生效过（见「视觉约定」），别再把它加回来。

### 视觉约定

2026-10-03 做过一次重设计，配色与版式都换过。改样式前先读 `assets/scss/devresume.scss`
顶部的 token 块。

- **只有两个值由 `config.toml` 注入**：`primaryColor` 与 `textPrimaryColor`，两个语言下各写
  一份、值相同。其余 token（正文色、次要色、强调色、纸面底、细线）在 SCSS 里写死。
- **不要用 `lighten()` 从主色推派生色**。旧版就是这么做的，推出来的浅色在正文尺寸下
  普遍不达 WCAG AA —— `.item-meta` 的 `lighten(主色, 40%)` = `#6f8ab6`，白底只有 3.51:1，
  而它是 12px。SCSS 里每个色值后面括号里标了白底对比度，改色照那个底线走。
- **字体只用系统栈**（`$font-family-sans-serif` 显式列了 CJK）。衬线 `$font-family-serif`
  **只给论文标题**，因为两个语言页里它都是英文。⚠️ 不要把含中文的元素放进衬线栈：
  Windows 上中文衬线默认落到宋体（SimSun），没有真 Bold，大字号会笔画发虚。
- **别用 `shadow-lg` 之类的 Bootstrap `!important` 工具类去叠卡片阴影** —— 它会静默压掉
  SCSS 里同属性的规则（`.resume-wrapper:hover` 就这么失效了整整一段时间没人发现）。
- 不显示的部件**以 HTML 注释保留**在模板里，不删除（以后可能还要用）。
- 改版式的请求常常是「只动被点名的那一项」—— 别顺手扩大范围。
- **模板里的 class 必须在 SCSS 里有定义**。此前 `.theme-bg-light` / `.lang-switch` /
  `.resume-list` 三个都是原主题残留的空类，白挂了好几年。