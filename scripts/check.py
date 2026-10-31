#!/usr/bin/env python3
"""教材自我檢查：python3 scripts/check.py

- 每段 Python 範例都要能被 Python 解析（語法正確）
- HTML 屬性沒有被巢狀引號切壞（例如 data-explain="…encoding="utf-8"…"）
- 每一題選擇題剛好有一個正確選項（data-ok="1"）
- 腳本裡用 $('#id') 取的元素都存在
"""
import ast
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "index.html"
ATTR_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.bad_attrs = set(), []
        self.questions, self._q_depth, self._depth = [], None, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for name, _ in attrs:
            if not ATTR_NAME.match(name) and name.lower() not in {"viewbox"}:
                self.bad_attrs.append((self.getpos()[0], tag, name))
        if "id" in a:
            self.ids.add(a["id"])
        if tag in {"br", "img", "input", "meta", "link", "hr"}:
            return
        self._depth += 1
        if tag == "div" and "q" in (a.get("class") or "").split():
            self.questions.append({"line": self.getpos()[0], "ok": 0, "options": 0})
            self._q_depth = self._depth
        if tag == "button" and self._q_depth is not None and self.questions:
            if "data-ok" in a:
                self.questions[-1]["options"] += 1
                self.questions[-1]["ok"] += a["data-ok"] == "1"

    def handle_endtag(self, tag):
        if tag in {"br", "img", "input", "meta", "link", "hr"}:
            return
        if self._q_depth is not None and self._depth == self._q_depth:
            self._q_depth = None
        self._depth -= 1


def main():
    src = PAGE.read_text(encoding="utf-8")
    errors = []

    blocks = re.findall(r'<pre class="[^"]*\bpy\b[^"]*"[^>]*>([\s\S]*?)</pre>', src)
    for i, block in enumerate(blocks, 1):
        code = html.unescape(re.sub(r"<[^>]+>", "", block))
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"第 {i} 段 Python 範例語法錯誤（第 {e.lineno} 行）：{e.msg}")

    c = Collector()
    c.feed(src)
    for line, tag, name in c.bad_attrs:
        errors.append(f"第 {line} 行 <{tag}> 出現奇怪的屬性「{name}」，多半是引號沒有跳脫")
    for q in c.questions:
        if q["options"] and q["ok"] != 1:
            errors.append(f"第 {q['line']} 行的題目有 {q['ok']} 個正確選項（應該剛好 1 個）")

    script = "\n".join(re.findall(r"<script>([\s\S]*?)</script>", src))
    for ref in sorted(set(re.findall(r"\$\('#([\w-]+)'\)", script))):
        if ref not in c.ids:
            errors.append(f"腳本用到 #{ref}，但頁面上沒有這個 id")

    questions = sum(1 for q in c.questions if q["options"])
    if errors:
        print("\n".join("✗ " + e for e in errors))
        return 1
    print(f"✓ {len(blocks)} 段 Python 範例、{questions} 題選擇題、{len(c.ids)} 個 id 檢查通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
