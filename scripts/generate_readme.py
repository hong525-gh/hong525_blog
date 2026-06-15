#!/usr/bin/env python3
"""
Generate README.md from local _posts/ Markdown files

功能说明：
  - 扫描 _posts/ 目录下的所有 Markdown 文件
  - 解析 YAML front matter，提取标题、日期、分类
  - 按创建时间倒序排列，提取置顶文章（categories 包含 pin）
  - 生成 README.md，包含置顶区、最近 10 篇文章列表、个人链接
"""
import re
from pathlib import Path
from datetime import datetime, timezone

POSTS_DIR = Path("_posts")
BASE_URL = "https://hong525-gh.github.io/hong525_blog"


def parse_front_matter(text: str) -> dict:
    """Parse simple YAML front matter from markdown text."""
    text = text.strip()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1].strip()
    result = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        # Handle quoted strings
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"')
        # Handle lists like [pin] or ["a", "b"]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                value = []
            else:
                items = []
                for item in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', inner):
                    item = item.strip()
                    if item.startswith('"') and item.endswith('"'):
                        item = item[1:-1].replace('\\"', '"')
                    items.append(item)
                value = items
        result[key] = value
    return result


def parse_post(filepath: Path) -> dict:
    """Parse a single post file and return metadata dict."""
    text = filepath.read_text(encoding="utf-8")
    fm = parse_front_matter(text)

    # Extract date and slug from filename: YYYY-MM-DD-slug.md
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md", filepath.name)
    if not m:
        return None
    date_str, slug = m.group(1), m.group(2)

    # Parse date from front matter if available, else from filename.
    # Jekyll converts all dates to UTC for URL generation, so we must do the same.
    date_raw = fm.get("date", date_str)
    date_clean = date_raw.strip()

    # Parse display date from the date part only (local date as written)
    display_dt = datetime.strptime(date_raw[:10], "%Y-%m-%d")
    display_date_str = display_dt.strftime("%Y-%m-%d")

    # Parse UTC date for URL generation — match Jekyll’s UTC conversion
    utc_dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M %z"):
        try:
            utc_dt = datetime.strptime(date_clean, fmt)
            break
        except ValueError:
            continue

    if utc_dt is None:
        # No timezone in frontmatter — treat as UTC (dates without timezone
        # are assumed to already be UTC by Jekyll)
        utc_dt = display_dt
    else:
        # Convert to UTC (for sorting / URL)
        utc_dt = utc_dt.astimezone(timezone.utc)

    categories = fm.get("categories", [])
    if isinstance(categories, str):
        categories = [categories]

    return {
        "title": fm.get("title", "Untitled"),
        "date": utc_dt,
        "date_str": display_date_str,
        "slug": slug,
        "categories": categories,
        "url": f"{BASE_URL}/{'/'.join(categories) + '/' if categories else ''}{utc_dt.strftime('%Y/%m/%d')}/{slug}.html",
        "filepath": filepath,
    }


def generate_readme():
    if not POSTS_DIR.exists():
        print(f"{POSTS_DIR} does not exist. Aborting.")
        return

    posts = []
    for filepath in sorted(POSTS_DIR.glob("*.md")):
        post = parse_post(filepath)
        if post:
            posts.append(post)

    posts.sort(key=lambda x: x["date"], reverse=True)
    pinned = [p for p in posts if "pin" in p["categories"]]

    lines = [
        "# 余烬",
        "",
        "_本分健康，认真努力。做对事情，知错即止。_",
        "",
        "我是 [Hong525](https://github.com/hong525-gh)，秉持 Stoic 的人生态度，喜欢跑步，乐于分享。",
        "",
        "> 你我不会在大街上逮着陌生人争论不休，那么同样的，你我不应该在互联网上做这种事情。",
        "",
        "",
        "",
        "## 置顶",
        "",
    ]

    if pinned:
        for post in pinned:
            lines.append(f'- [{post["title"]}]({post["url"]}) -- {post["date_str"]}')
    else:
        lines.append("（暂无）")

    lines.extend(["", "## 最近更新", ""])

    for post in posts[:10]:
        lines.append(f'- [{post["title"]}]({post["url"]}) -- {post["date_str"]}')

    if not posts:
        lines.append("（暂无）")

    lines.extend([
        "",
        "## 链接",
        "",
        "- [Home](https://hong525-gh.github.io/hong525_blog)",
        "- [GitHub](https://github.com/hong525-gh)",
        "- [Twitter](https://x.com/hong525_x)",
        "- [Telegram 频道](https://t.me/ciceros_self_talk)",
        "",
        "---",
        "",
        '*"On the Internet, nobody knows you\'re a dog."*',
        "",
    ])

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"README.md generated from {len(posts)} posts.")


if __name__ == "__main__":
    generate_readme()
