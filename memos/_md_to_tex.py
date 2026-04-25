"""Markdown -> LaTeX converter tuned for this repo's memos.

Usage: python memos/_md_to_tex.py memos/01_pitch_framing.md > memos/01_pitch_framing.tex

Handles: H1/H2/H3 headings, paragraphs, bold/italic, inline code, code
fences, simple GitHub-flavoured tables, bullet/numbered lists, blockquotes,
[link](url). Wraps in this repo's standard preamble. Does NOT try to render
inline math or images perfectly -- the heavy memos (07/08/13/16/17) are
hand-written .tex.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

UNICODE_REPLACEMENTS = {
    "—": "---",
    "–": "--",
    "→": r"$\to$",
    "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$",
    "⇒": r"$\Rightarrow$",
    "≥": r"$\geq$",
    "≤": r"$\leq$",
    "≠": r"$\neq$",
    "≈": r"$\approx$",
    "×": r"$\times$",
    "·": r"$\cdot$",
    "±": r"$\pm$",
    "°": r"\textdegree{}",
    "λ": r"$\lambda$",
    "μ": r"$\mu$",
    "σ": r"$\sigma$",
    "α": r"$\alpha$",
    "β": r"$\beta$",
    "Δ": r"$\Delta$",
    "δ": r"$\delta$",
    "π": r"$\pi$",
    "θ": r"$\theta$",
    "‐": "-",
    "−": "-",
    "•": r"\textbullet{}",
    "…": "\\ldots",
    "❌": "no",
    "✅": "yes",
    "✓": r"\checkmark{}",
    "✗": r"$\times$",
    "★": "*",
    "☆": "*",
    "→": r"$\to$",
    "←": r"$\leftarrow$",
    "■": r"\textbullet{}",
    "□": "[ ]",
    "“": "``",
    "”": "''",
    "‘": "`",
    "’": "'",
    " ": " ",  # non-breaking space
    "$": r"\$",
}


def _esc(s: str) -> str:
    # First substitute Unicode -> LaTeX commands.
    for src, dst in UNICODE_REPLACEMENTS.items():
        s = s.replace(src, dst)
    out = []
    for ch in s:
        out.append(LATEX_SPECIALS.get(ch, ch))
    return "".join(out)


def _inline(s: str) -> str:
    """Convert inline markdown -> LaTeX inside a paragraph."""
    # Pull out code spans and links first to protect contents.
    placeholders: list[str] = []

    def _stash(payload: str) -> str:
        placeholders.append(payload)
        return f"\x00{len(placeholders) - 1}\x00"

    # ``code`` and `code` (inline). Use \code{...} with detokenize.
    s = re.sub(r"``([^`]+)``", lambda m: _stash(rf"\code{{{m.group(1)}}}"), s)
    s = re.sub(r"`([^`]+)`", lambda m: _stash(rf"\code{{{m.group(1)}}}"), s)

    # [text](url) -> \href{url}{text}
    def _link(m):
        text = _esc(m.group(1))
        url = m.group(2).replace("\\", "/").replace(" ", "%20")
        # Internal memo links: keep relative path; external: escape
        return _stash(rf"\href{{{url}}}{{{text}}}")

    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, s)

    # Now escape everything else.
    s = _esc(s)

    # Restore placeholders.
    def _restore(m):
        idx = int(m.group(1))
        return placeholders[idx]

    s = re.sub(r"\x00(\d+)\x00", _restore, s)

    # Bold: **text** -> \textbf{text}; italic: *text* -> \emph{text}
    s = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", s)
    return s


def _convert_table(lines: list[str]) -> str:
    """GitHub-flavoured pipe table -> tabular."""
    if not lines:
        return ""
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines
    ]
    # rows[0] = header, rows[1] = alignment, rows[2:] = body
    header, body = rows[0], rows[2:]
    n = len(header)
    spec = "l" * n
    out = ["\\begin{center}", "\\begin{tabular}{" + spec + "}", "\\toprule"]
    out.append(" & ".join(_inline(h) for h in header) + " \\\\")
    out.append("\\midrule")
    for r in body:
        # pad ragged rows
        r = (r + [""] * n)[:n]
        out.append(" & ".join(_inline(c) for c in r) + " \\\\")
    out.append("\\bottomrule")
    out.append("\\end{tabular}")
    out.append("\\end{center}")
    return "\n".join(out) + "\n"


def convert(md_text: str, title: str | None = None, memo_num: str | None = None) -> str:
    """Convert markdown text to a complete LaTeX document."""
    lines = md_text.splitlines()
    body: list[str] = []
    i = 0

    # Title from first H1, if present, unless overridden.
    detected_title = None
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            detected_title = line[2:].strip()
            i += 1
            break
        elif line.strip():
            break
        else:
            i += 1
    title = title or detected_title or "Memo"
    if "—" in title and memo_num is None:
        # Look for "NN — Subject" pattern
        m = re.match(r"^(\d+)\s*—\s*(.*)$", title)
        if m:
            memo_num = m.group(1)
            title = m.group(2).strip()

    # --- body conversion ---
    in_code = False
    code_buf: list[str] = []
    while i < len(lines):
        line = lines[i]

        # Code fence
        if line.strip().startswith("```"):
            if in_code:
                body.append("\\begin{lstlisting}")
                # Sanitize unicode inside code listings -- listings doesn't
                # accept arbitrary UTF-8 without literate config.
                ascii_replacements = {
                    "—": "--", "–": "-", "→": "->", "←": "<-",
                    "≥": ">=", "≤": "<=", "≠": "!=", "≈": "~=",
                    "×": "x", "·": ".", "±": "+/-", "…": "...",
                    "“": '"', "”": '"', "‘": "'", "’": "'", " ": " ",
                    "−": "-", "‐": "-",
                }
                for raw in code_buf:
                    for src, dst in ascii_replacements.items():
                        raw = raw.replace(src, dst)
                    # Final safety: drop any remaining non-ASCII
                    raw = raw.encode("ascii", "replace").decode("ascii").replace("?", "")
                    body.append(raw)
                body.append("\\end{lstlisting}")
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Headings
        if line.startswith("### "):
            body.append("\\subsubsection*{" + _inline(line[4:].strip()) + "}")
            i += 1
            continue
        if line.startswith("## "):
            body.append("\\section{" + _inline(line[3:].strip()) + "}")
            i += 1
            continue
        if line.startswith("# "):
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(lines[i].lstrip(">").strip())
                i += 1
            body.append("\\begin{quote}")
            body.append(_inline(" ".join(quote_lines)))
            body.append("\\end{quote}")
            continue

        # Tables (line starts with '|' and next line is '|---|...')
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s|:-]+\|\s*$", lines[i + 1]):
            tbl = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            body.append(_convert_table(tbl))
            continue

        # Bullet list
        if re.match(r"^\s*[-*+]\s", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s", "", lines[i]).rstrip())
                i += 1
            body.append("\\begin{itemize}")
            for it in items:
                body.append("  \\item " + _inline(it))
            body.append("\\end{itemize}")
            continue

        # Numbered list
        if re.match(r"^\s*\d+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s", "", lines[i]).rstrip())
                i += 1
            body.append("\\begin{enumerate}")
            for it in items:
                body.append("  \\item " + _inline(it))
            body.append("\\end{enumerate}")
            continue

        # Horizontal rule
        if re.match(r"^\s*-{3,}\s*$", line) or re.match(r"^\s*\*{3,}\s*$", line):
            body.append("\\medskip\\hrule\\medskip")
            i += 1
            continue

        # Paragraph: collect until blank line
        if line.strip():
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not (
                lines[i].startswith("#")
                or lines[i].lstrip().startswith("|")
                or re.match(r"^\s*[-*+\d]\s", lines[i])
                or lines[i].startswith(">")
                or lines[i].strip().startswith("```")
            ):
                para.append(lines[i])
                i += 1
            body.append(_inline(" ".join(p.strip() for p in para)))
            body.append("")
            continue

        # Blank
        i += 1

    if memo_num:
        full_title = f"\\textbf{{{_esc(title)}}}\\\\\n\\large Memo {memo_num}"
    else:
        full_title = f"\\textbf{{{_esc(title)}}}"

    return r"""\documentclass[11pt]{article}
\input{_preamble}

\title{""" + full_title + r"""}
\author{Bloomsbury Tech -- Agentic Payments Hackathon Build}
\date{April 25, 2026}

\begin{document}
\maketitle

""" + "\n".join(body).rstrip() + r"""

\end{document}
"""


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python memos/_md_to_tex.py <input.md>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    sys.stdout.write(convert(path.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
