# -*- coding: utf-8 -*-
"""Parse HelloGitHub monthly issue Markdown into structured Python dicts.

Source format (content/HelloGitHubNNN.md in 521xueweihan/HelloGitHub), current
"web" flavor on master:

    # 《HelloGitHub》第 124 期
    > 兴趣是最好的老师，**HelloGitHub** 让你对开源感兴趣！
    <p align="center"><img ...></p>          <- HTML, skipped
    ## 目录
    ...
    ## 内容
    ### C 项目
    1、[86Box](https://hellogithub.com/periodical/statistics/click?target=https://github.com/...)：描述...
    <p align="center"><img ...></p>          <- HTML, skipped
    ### C# 项目
    ...
    ## 赞助
    <table>...</table>                        <- HTML, skipped
    ## 声明

The parser also tolerates the older "compact" flavor (title and tagline on one
line, "来自 [@user](...) 的分享" contributor suffixes, "『上一期』..." footers).
"""

import re
from urllib.parse import parse_qs, urlparse

ENTRY_RE = re.compile(
    r"^\s*(\d+)、\s*\[([^\]]+)\]\(([^)]*)\)\s*(?:[：:]\s*)?(.*)$"
)
HEADING_RE = re.compile(r"^###\s+(.*)$")
TITLE_RE = re.compile(r"^#\s+(.+)$")
AUTHOR_RE = re.compile(r"来自\s*\[@?([^\]]+)\]\([^)]*\)\s*的分享\s*$")
FOOTER_MARKERS = ("『上一期』", "『下一期』", "反馈和建议", "来！推荐开源项目")
END_SECTIONS = ("赞助", "声明", "联系")

DEFAULT_CATEGORY = "未分类"

IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)")
QUOTE_RE = re.compile(r"^>\s?")


def extract_url(link):
    """Unwrap HelloGitHub tracking links to the real GitHub URL."""
    if "hellogithub.com/periodical/statistics/click" in link:
        qs = parse_qs(urlparse(link).query)
        target = qs.get("target")
        if target:
            return target[0]
    return link.strip()


def md_to_text(text):
    """Minimal markdown-to-plain-text cleanup (no content changes)."""
    text = IMAGE_RE.sub(r"\1", text)
    text = LINK_RE.sub(r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = ITALIC_RE.sub(r"\1", text)
    text = text.replace("`", "")
    text = QUOTE_RE.sub("", text)
    return text.strip()


def _close_entry(categories, entry):
    """Append an accumulated entry to its category (create it if needed)."""
    name = md_to_text(entry["name"])
    if not name:
        return
    cat_name = entry.get("category") or DEFAULT_CATEGORY
    category = None
    for c in categories:
        if c["name"] == cat_name:
            category = c
            break
    if category is None:
        category = {"name": cat_name, "projects": []}
        categories.append(category)

    text = "\n".join(entry["lines"]).strip()

    author = ""
    m = AUTHOR_RE.search(text)
    if m:
        author = m.group(1).strip()
        text = text[: m.start()].strip()

    lines_out = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            lines_out.append("")
            continue
        if in_fence:
            lines_out.append(line)
        else:
            lines_out.append(md_to_text(line))
    description = "\n".join(lines_out)
    # collapse 3+ consecutive blank lines down to 2
    description = re.sub(r"\n{3,}", "\n\n", description).strip()

    category["projects"].append(
        {
            "name": name,
            "url": extract_url(entry["url"]),
            "description": description,
            "author": author,
        }
    )


def parse_issue(text, issue_id):
    """Parse one issue's Markdown text into an issue dict."""
    title = ""
    categories = []
    current_entry = None
    current_category = None
    in_code = False
    started = False  # seen at least one category heading or entry

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if any(marker in line for marker in FOOTER_MARKERS):
            break

        # Issue title (first H1 line)
        if not title:
            m = TITLE_RE.match(line)
            if m:
                title = m.group(1).split(">")[0].strip()
                continue

        # Stop at trailing sections (sponsors / license) once content started
        m = re.match(r"^##\s+(.*)$", line)
        if m and started and m.group(1).strip() not in ("目录", "内容"):
            break

        # Code fences inside an entry description
        if line.startswith("```"):
            if current_entry is not None:
                current_entry["lines"].append(line)
                in_code = not in_code
            continue
        if in_code:
            if current_entry is not None:
                current_entry["lines"].append(line)
            continue

        # HTML blocks (images, sponsor tables, <p>/<br>/<img>) are not content
        if line.startswith("<"):
            continue

        # Category heading, possibly followed by an entry on the same line
        m = HEADING_RE.match(line)
        if m:
            rest = m.group(1)
            m2 = re.search(r"\d+、\s*\[", rest)
            if m2:
                heading = rest[: m2.start()].strip()
                remainder = rest[m2.start():]
            else:
                heading = rest.strip()
                remainder = ""
            if heading:
                started = True
                current_category = heading
                if current_entry is not None:
                    _close_entry(categories, current_entry)
                    current_entry = None
                if not any(c["name"] == heading for c in categories):
                    categories.append({"name": heading, "projects": []})
                if remainder:
                    me = ENTRY_RE.match(remainder)
                    if me:
                        current_entry = {
                            "category": heading,
                            "name": me.group(2),
                            "url": me.group(3),
                            "lines": [me.group(4)],
                        }
            continue

        # Entry start: "N、[name](url)：description"
        me = ENTRY_RE.match(line)
        if me:
            started = True
            if current_entry is not None:
                _close_entry(categories, current_entry)
            current_entry = {
                "category": current_category,  # may be None -> 未分类
                "name": me.group(2),
                "url": me.group(3),
                "lines": [me.group(4)],
            }
            continue

        # Continuation of the current entry's description
        if current_entry is not None:
            current_entry["lines"].append(line)

    if current_entry is not None:
        _close_entry(categories, current_entry)

    if not title:
        title = "《HelloGitHub》第 %s 期" % issue_id

    return {
        "id": int(issue_id),
        "title": title,
        "categories": [c for c in categories if c["projects"]],
    }