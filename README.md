# HelloGitHub 项目展示

一个纯静态网站，展示 [HelloGitHub](https://github.com/521xueweihan/HelloGitHub) 月刊中的开源项目，
**按编程语言/分类分组展示**，默认显示最新一期，并支持全部历史期号（1–124 期）切换浏览。

- 零构建依赖：数据管道仅用 Python 标准库，前端为原生 HTML/CSS/JS，无需 Node.js。
- 数据来源：自动抓取 HelloGitHub 仓库 `content/HelloGitHubNNN.md` 并解析为结构化 JSON。

## 项目结构

```
.
├── index.html          # 页面入口
├── style.css           # 样式
├── app.js              # 前端逻辑（加载 JSON、按分类渲染、期号切换）
├── data/
│   └── issues.json     # 生成的数据（已提交，前端直接读取）
├── scripts/
│   ├── parser.py       # 月刊 Markdown 解析器（可复用）
│   └── build_data.py   # 数据管道：下载 + 解析 + 生成 issues.json
└── tests/
    ├── fixtures/       # 第 1/100/124 期真实内容快照
    ├── test_parser.py  # 解析器单元测试
    └── test_integration.py  # 全量数据校验（含可选联网重建）
```

## 使用方式

### 1. 本地预览（推荐）

```powershell
python -m http.server 8000
```

然后浏览器打开 <http://localhost:8000>。

> 说明：前端通过 `fetch("data/issues.json")` 读取数据，直接双击打开 `index.html`
> （`file://` 协议）可能因浏览器安全策略无法加载 JSON，请用本地服务器访问。

### 2. 重新生成数据（HelloGitHub 每月更新一期后）

```powershell
python scripts/build_data.py
```

脚本会优先尝试一次性下载仓库 tar 包（`codeload.github.com`），失败时自动降级为
GitHub API + raw 逐文件下载。生成结果写入 `data/issues.json`（覆盖）。

可选参数：

```powershell
python scripts/build_data.py --source tarball   # 仅用 tar 包方式
python scripts/build_data.py --source raw       # 仅用 raw 方式
python scripts/build_data.py --out other.json   # 自定义输出路径
```

### 3. 运行测试

```powershell
python -m unittest discover -s tests -v
```

- `test_parser.py`：解析器单元测试（基于真实内容快照）。
- `test_integration.py`：全量数据校验；其中联网重建测试在网络不可用时会自动跳过。

## 数据模型

`data/issues.json` 结构：

```json
{
  "updatedAt": "2026-08-04",
  "source": "https://github.com/521xueweihan/HelloGitHub",
  "issues": [
    {
      "id": 124,
      "title": "《HelloGitHub》第 124 期",
      "categories": [
        {
          "name": "Python 项目",
          "projects": [
            {
              "name": "msgspec",
              "url": "https://github.com/msgspec/msgspec",
              "description": "更快的 Python 序列化库……",
              "author": ""
            }
          ]
        }
      ]
    }
  ]
}
```

## 更新流程（每月）

1. HelloGitHub 发布新一期后，运行 `python scripts/build_data.py`；
2. 检查输出统计（期数、最新期号、项目总数）；
3. 运行 `python -m unittest discover -s tests -v` 确认无回归；
4. 提交 `data/issues.json` 的变更即可，前端无需改动。

## 部署

v1 以本地预览为主。如需上线（如 GitHub Pages）：

1. 将本仓库推送到 GitHub；
2. 在仓库 Settings → Pages 中选择分支的根目录作为发布源；
3. 站点为纯静态，无需服务器。

## 版权与许可

内容来自 [HelloGitHub](https://github.com/521xueweihan/HelloGitHub)，采用
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.zh)
（署名-非商业使用-禁止演绎）许可。本站仅供非商业展示，保留署名，原文未做修改。