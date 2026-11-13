# LLM4Rail — 大语言模型能在多大程度上帮助求解铁路优化问题?

[English](README.md) | **简体中文**

LLM4Rail 研究网站。这是一个面向 GitHub Pages 的静态站点:无需构建,无任何依赖。

## 目录结构

- `index.html` — 英文概览页:研究问题、问题库、差距图、方法、验证、路线图、引用
- `instances/` — 可搜索的 166 个算例目录(英文)
- `zh/index.html`、`zh/instances/` — 上述两个页面的中文版
- `assets/js/i18n.js` — 表格与图表的中英文标签(算例集、状态、单位)
- `data/instances.json`、`data/instances.csv` — 可下载的算例数据
- `assets/js/data.js` — 页面加载的同一份数据(可在 `file://` 下直接打开)
- `assets/css/site.css` — 全部样式;品牌色定义为文件顶部的 CSS 变量
- `assets/img/` — Logo 文件;`favicon.*` 与 `apple-touch-icon.png` 位于根目录

## 部署

1. 正式公开地址为 [LLM4Rail GitHub Pages](https://llm4rail.github.io/)，发布源为 `LLM4Rail/llm4rail.github.io`。组织使用私有仓库发布 Pages 需要支持该功能的 GitHub 套餐。
2. 在 Settings → Pages 中选择 "Deploy from a branch"，分支选 `main`，目录选 `/ (root)`。
3. 将站点文件推送到 `main` 分支。

## 发布前

替换以下占位符:

- 作者已填写;单位有意留空,如需添加,请修改 `index.html` 与 `zh/index.html` 首屏的作者行
- 若仓库位于其他位置,修改 `https://github.com/LLM4Rail/llm4rail.github.io`
- 若计划变动,修改第 06 节路线图中的日期
- 新闻条目的日期(中英文)

静态文本写在各语言的 HTML 中;修改其中一个时,请保持 `index.html` 与 `zh/index.html` 同步。

## 更新数据

编辑 `data/instances.json` 后，用以下命令同时重新生成 CSV 下载文件和网站的 JavaScript 数据。

```sh
python3 scripts/export_instances.py
```

- `library` 和 `instance` 共同标识一个目录条目。同一 `family` 标记已确认的同源模型，各模型分别计入条目数。
- `n1` 和 `n2` 表示事件数与活动数（`ev_act`）、列车数与作业数（`tr_op`），或变量数与约束数（`var_con`）。
- `record`、`source` 和 `upper_evidence` 描述 `best_known`。`bound_record`、`bound_source` 和 `bound_evidence` 描述 `best_bound`。
- `gap` 为上下界之差除以上界绝对值，上下界相等时为零。`status` 取值为 `open`（未证明最优）、`optimal`（已证明最优）或 `no_bound`（无公开下界）。集合、状态和证据代码的双语标签位于 `assets/js/i18n.js`。

结果通过验证后，更新对应数值及证据字段，同步 `gap`、`status` 和两种语言页面的统计。发布本项目结果时，更新 `llm4rail` 并在 `i18n.js` 中添加双语标签。

## 数据来源

- PESPlib 记录表:https://timpasslib.aalto.fi/pesplib.html(读取于 2026-11-11)
- MIPLIB 2017 Easy、Hard 标签及第 37 版解文件：https://miplib.zib.de/download.html
- TimPassLib 解页面:https://timpasslib.aalto.fi/solutions.html(读取于 2026-11-11)
- DISPLIB:https://displib.github.io/(仓库 github.com/displib/displib.github.io,最后更新 2025-09-18)
- DISPLIB 论文结果见 [Fuchs 等附录 B](https://doi.org/10.1016/j.jrtpm.2026.100600)和 [Stärk 等附录 A](https://doi.org/10.4230/OASIcs.ATMOS.2026.6)
