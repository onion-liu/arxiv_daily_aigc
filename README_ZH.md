# Arxiv Daily AIGC

这是一个自动化项目，旨在每日从 arXiv 获取计算机视觉（cs.CV）领域的最新论文，使用 AI (目前通过 OpenRouter API) 筛选出与图像/视频/多模态生成相关的论文，并将结果生成为结构化的 JSON 数据和美观的 HTML 页面，最终通过 GitHub Actions 自动部署到 GitHub Pages。

## 功能

1.  **数据抓取**: 每日自动从 arXiv 获取 `cs.CV` 领域的最新论文。
2.  **AI 筛选**: 利用 LLM 智能筛选与图像/视频/多模态生成主题相关的论文，并分维度对论文价值进行打分。
3.  **数据存储**: 将筛选后的论文信息（标题、摘要、链接等）保存为日期命名的 JSON 文件（存放于 `daily_json/` 目录）。
4.  **网页生成**: 根据 JSON 数据，使用预设模板生成每日的 HTML 报告（存放于 `daily_html/` 目录），并更新主入口页面 `index.html`。
5.  **自动化部署**: 通过 GitHub Actions 实现每日定时执行抓取、筛选、生成和部署到 GitHub Pages 的完整流程。

## 技术栈

*   **后端/脚本**: Python 3.x (`arxiv`, `requests`, `jinja2`)
*   **前端**: HTML5, TailwindCSS (CDN), JavaScript, Framer Motion (CDN)
*   **自动化**: GitHub Actions
*   **部署**: GitHub Pages

## 安装

1.  **克隆仓库**:
    ```bash
    git clone <your-repository-url>
    cd arxiv_daily_aigc
    ```

2.  **创建并激活虚拟环境** (推荐):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # 或者 .\.venv\Scripts\activate # Windows
    ```

3.  **安装依赖**: 项目所需的所有 Python 库都列在 `requirements.txt` 文件中。
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置 API Key**: 此项目需要 OpenRouter API Key 来进行 AI 筛选，当然你也可以通过修改 `src/filter.py` 调用其他LLM API。为了安全起见，请勿将 Key 硬编码在代码中。在本地运行时，可以通过环境变量设置；在 GitHub Actions 中，请将其设置为名为 `OPENROUTER_API_KEY` 的 Secret。

## 使用

### 本地运行

可以直接运行主脚本 `main.py` 来手动触发一次完整的流程（抓取、筛选、生成）。

```bash
# 确保设置了 OPENROUTER_API_KEY 环境变量
export OPENROUTER_API_KEY='your_openrouter_api_key'

# 运行主脚本 (默认处理当天的论文)
python src/main.py

# (可选) 指定日期运行
# python src/main.py --date YYYY-MM-DD
```

运行成功后：
*   当天的 JSON 数据会保存在 `daily_json/YYYY-MM-DD.json`。
*   当天的 HTML 报告会保存在 `daily_html/YYYY_MM_DD.html`。
*   主入口页面 `index.html` 会被更新以包含最新的报告链接。

可以直接在浏览器中打开 `index.html` 查看结果。

### GitHub Actions 自动化

仓库中已配置好 GitHub Actions 工作流 (`.github/workflows/daily_arxiv.yml`)。

*   **定时触发**: 该工作流默认设置为每天定时自动运行。
*   **手动触发**: 你也可以在 GitHub 仓库的 Actions 页面手动触发此工作流。

工作流会自动完成所有步骤，并将生成的 `index.html`, `daily_json/`, `daily_html/` 目录下的文件部署到 GitHub Pages。

## 查看部署结果

项目配置为通过 GitHub Pages 展示结果。请访问你的 GitHub Pages URL (通常是 `https://<your-username>.github.io/<repository-name>/`) 查看每日更新的论文报告。

## 文件结构

```
.
├── .github/workflows/daily_arxiv.yml  # GitHub Actions 配置文件
├── src/                     # Python 脚本目录
│   ├── main.py              # 主执行脚本
│   ├── scraper.py           # ArXiv 爬虫模块
│   ├── filter.py            # OpenRouter 过滤模块
│   └── html_generator.py    # HTML 生成模块
├── templates/               # HTML 模板目录
│   └── paper_template.html
├── daily_json/              # 存放每日 JSON 结果
├── daily_html/              # 存放每日 HTML 结果
├── index.html               # GitHub Pages 入口页面
├── requirements.txt         # Python 依赖列表
├── README.md                # 项目说明文件
└── TODO.md                  # 项目待办事项
```

## 感谢
- 本项目的灵感最初源于[fortunechen](https://github.com/fortunechen)的一次分享
- 本项目绝大多数代码由Trae/Cursor生成，感谢他们的任劳任怨和孜孜不倦😄
