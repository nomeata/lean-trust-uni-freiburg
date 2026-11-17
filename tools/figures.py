#!/usr/bin/env python3
"""Generate the SVG figures of the deck (style after Leo's SViL 2026 deck).

Usage: python3 tools/figures.py   (writes static/images/*.svg)
"""
import hashlib
import json
import os
import re
import subprocess
import tempfile
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "static", "images")

FONT = "'Source Sans 3', 'Helvetica Neue', Arial, sans-serif"
MONO = "'SF Mono', Menlo, Monaco, Consolas, monospace"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#94a3b8"
BLUE = "#0073A3"
TEAL = "#0891b2"
BLUE_BG = "#eff6ff"
BLUE_LINE = "#93c5fd"
CODE_BG = "#f8fafc"
CODE_LINE = "#e2e8f0"
RED = "#dc2626"
RED_BG = "#fef2f2"
GREEN = "#15803d"
GREEN_BG = "#ecfdf5"
KW = "#cf222e"
CONST = "#0550ae"


def svg(w, h, title, body):
    # aria-label rather than <title>: a <title> shows up as a hover tooltip on the slide.
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{escape(title)}" font-family="{FONT}">\n' + "\n".join(body) + "\n</svg>\n")


def text(x, y, s, size=26, weight=400, fill=INK, anchor="middle", mono=False, extra=""):
    fam = f' font-family="{MONO}"' if mono else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{fam}{extra}>{s}</text>')


def rect(x, y, w, h, rx=10, fill="#ffffff", stroke=None, sw=1.5, extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}{extra}/>'


def arrow(x1, y1, x2, y2, color=LINE, sw=3, head=12, dash=False):
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(a), y2 - head * math.sin(a)
    px, py = head * 0.6 * -math.sin(a), head * 0.6 * math.cos(a)
    d = ' stroke-dasharray="8 6"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="{sw}"{d}/>'
            f'<polygon points="{x2},{y2} {bx + px:.1f},{by + py:.1f} {bx - px:.1f},{by - py:.1f}" fill="{color}"/>')


def code(x, y, lines, size=22, w=None, lh=1.45):
    """A code box; lines are lists of (text, color, weight) runs or plain strings."""
    h = int(len(lines) * size * lh + size * 0.9)
    out = [rect(x, y, w, h, rx=8, fill=CODE_BG, stroke=CODE_LINE)]
    for i, line in enumerate(lines):
        runs = [(line, INK, 400)] if isinstance(line, str) else line
        spans = "".join(f'<tspan fill="{c}" font-weight="{wt}">{escape(t)}</tspan>' for t, c, wt in runs)
        out.append(f'<text x="{x + 14}" y="{y + size * 1.15 + i * size * lh:.1f}" font-size="{size}" '
                   f'font-family="{MONO}" fill="{INK}" xml:space="preserve">{spans}</text>')
    return out, h


# ── Why Lean: eight cards ──────────────────────────────────────────────

def why_lean():
    W, H = 1600, 780
    cw, ch, gap = 370, 360, 40
    cards = []

    def card(col, row, label):
        x, y = col * (cw + gap), row * (ch + gap + 20)
        cards.extend([
            rect(x, y, cw, ch, rx=16, fill="#ffffff", stroke=TEAL, sw=3),
            f'<path d="M{x} {y + 64} V{y + 16} Q{x} {y} {x + 16} {y} H{x + cw - 16} '
            f'Q{x + cw} {y} {x + cw} {y + 16} V{y + 64} Z" fill="{TEAL}"/>',
            text(x + cw / 2, y + 44, escape(label), size=30, weight=700, fill="#ffffff"),
        ])
        return x + 20, y + 90, cw - 40  # body origin and width

    kw = lambda s: (s, KW, 700)
    cn = lambda s: (s, CONST, 400)
    pl = lambda s: (s, INK, 400)

    # 1 Correctness
    x, y, w = card(0, 0, "Correctness")
    c, h = code(x, y, [[kw("theorem"), pl(" primes :")], [pl("  ∀ n, ∃ p > n,")], [pl("    "), cn("IsPrime"), pl(" p")]], w=w)
    cards += c
    cards.append(rect(x + 40, y + h + 30, w - 80, 56, rx=28, fill=GREEN_BG, stroke=GREEN, sw=2))
    cards.append(text(x + w / 2, y + h + 67, "✓  No goals", size=26, weight=600, fill=GREEN))

    # 2 Assistance
    x, y, w = card(1, 0, "Assistance")
    c, h = code(x, y, [[pl("  "), kw("exact?")]], w=w)
    cards += c
    cards.append(arrow(x + w / 2, y + h + 8, x + w / 2, y + h + 48, color=TEAL))
    c2, h2 = code(x, y + h + 58, [[pl("Try this:")], [pl("  "), kw("exact"), pl(" "), cn("Nat.dvd_refl"), pl(" n")]], w=w)
    cards += c2

    # 3 Early feedback
    x, y, w = card(2, 0, "Early feedback")
    c, h = code(x, y, [[pl("  "), kw("simp"), pl(" ["), cn("factorial"), pl("]")]], w=w)
    cards += c
    cards.append(f'<path d="M{x + 40} {y + h - 10} ' + " ".join(
        f"q 5 {(-6 if i % 2 else 6)} 10 0" for i in range(18)) + f'" fill="none" stroke="{RED}" stroke-width="2.5"/>')
    cards.append(rect(x, y + h + 30, w, 112, rx=8, fill=RED_BG, stroke="#fca5a5"))
    cards.append(text(x + 14, y + h + 66, "unsolved goals", size=22, fill=RED, anchor="start", mono=True))
    cards.append(text(x + 14, y + h + 104, "⊢ 0 &lt; n !", size=22, fill=INK, anchor="start", mono=True))

    # 4 Refactoring
    x, y, w = card(3, 0, "Refactoring")
    cards.append(rect(x, y, w, 40, rx=6, fill=RED_BG))
    cards.append(text(x + 12, y + 28, "- def IsPrime …", size=22, fill=RED, anchor="start", mono=True))
    cards.append(rect(x, y + 46, w, 40, rx=6, fill=GREEN_BG))
    cards.append(text(x + 12, y + 74, "+ def Nat.Prime …", size=22, fill=GREEN, anchor="start", mono=True))
    # dependents re-checked
    root = (x + w / 2, y + 130)
    cards.append(rect(root[0] - 70, root[1] - 22, 140, 44, rx=8, fill=BLUE_BG, stroke=BLUE_LINE))
    cards.append(text(root[0], root[1] + 8, "Nat.Prime", size=20, mono=True, fill=CONST))
    for i, bad in enumerate([False, True, False, True, False]):
        cx = x + 22 + i * (w - 44) / 4
        cards.append(f'<line x1="{root[0]}" y1="{root[1] + 22}" x2="{cx}" y2="{y + 210}" stroke="{LINE}" stroke-width="2"/>')
        cards.append(f'<circle cx="{cx}" cy="{y + 222}" r="13" fill="{RED if bad else GREEN}"/>')

    # 5 Search
    x, y, w = card(0, 1, "Search")
    cards.append(rect(x, y, w, 56, rx=28, fill="#ffffff", stroke=LINE, sw=2))
    cards.append(f'<circle cx="{x + 28}" cy="{y + 26}" r="10" fill="none" stroke="{MUTED}" stroke-width="3"/>'
                 f'<line x1="{x + 35}" y1="{y + 33}" x2="{x + 44}" y2="{y + 42}" stroke="{MUTED}" stroke-width="3"/>')
    cards.append(text(x + 56, y + 36, "_*(_+_) = _*_+_*_", size=20, anchor="start", mono=True))
    cards.append(arrow(x + w / 2, y + 66, x + w / 2, y + 106, color=TEAL))
    c, h = code(x, y + 116, [[cn("Nat.mul_add")], [pl(" : x*(y+z)")], [pl("   = x*y+x*z")]], w=w, size=21)
    cards += c

    # 6 Consistent definitions
    x, y, w = card(1, 1, "Consistent definitions")
    hub = (x + w / 2, y + 120)
    for i in range(7):
        import math
        a = math.pi * (0.1 + 0.8 * i / 6)
        ex, ey = hub[0] + 150 * math.cos(a) * 1.0, hub[1] - 0 + 100 * math.sin(a) * -1
        cards.append(f'<line x1="{hub[0]}" y1="{hub[1]}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="{LINE}" stroke-width="2"/>')
        cards.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="11" fill="{BLUE_BG}" stroke="{BLUE_LINE}" stroke-width="2"/>')
    for i in range(3):
        ex = x + 60 + i * (w - 120) / 2
        cards.append(f'<line x1="{hub[0]}" y1="{hub[1]}" x2="{ex:.0f}" y2="{y + 230}" stroke="{LINE}" stroke-width="2"/>')
        cards.append(f'<circle cx="{ex:.0f}" cy="{y + 230}" r="11" fill="{BLUE_BG}" stroke="{BLUE_LINE}" stroke-width="2"/>')
    cards.append(rect(hub[0] - 85, hub[1] - 26, 170, 52, rx=10, fill=BLUE, extra=""))
    cards.append(text(hub[0], hub[1] + 9, "Nat.Prime", size=24, weight=600, mono=True, fill="#ffffff"))

    # 7 Collaboration at scale
    x, y, w = card(2, 1, "Collaboration at scale")
    cards.append(text(x + w / 2, y + 120, "750+", size=96, weight=700, fill=BLUE))
    cards.append(text(x + w / 2, y + 175, "Mathlib contributors", size=26, fill=MUTED))
    cards.append(text(x + w / 2, y + 215, "2.4M+ lines", size=26, fill=MUTED))

    # 8 Trust bottleneck
    x, y, w = card(3, 1, "Trust bottleneck")
    for i, who in enumerate(["Coauthor", "Student", "AI"]):
        yy = y + 10 + i * 80
        cards.append(rect(x, yy, 130, 52, rx=26, fill=CODE_BG, stroke=LINE))
        cards.append(text(x + 65, yy + 34, who, size=22))
        cards.append(arrow(x + 132, yy + 26, x + 200, y + 116, color=LINE, sw=2.5))
    cards.append(rect(x + 204, y + 80, w - 204, 72, rx=12, fill=BLUE))
    cards.append(text(x + 204 + (w - 204) / 2, y + 126, "Lean ✓", size=28, weight=700, fill="#ffffff"))

    return svg(W, H, "Why Lean: correctness, assistance, early feedback, refactoring, search, "
               "consistent definitions, collaboration at scale, trust bottleneck", cards)


# ── Type theory as syntactic sugar for set theory ──────────────────────

MATH = "'STIX Two Math', 'Cambria Math', 'Latin Modern Math', 'Times New Roman', serif"


# ── Formulas, typeset by LaTeX ──────────────────────────────────────────────
# tex(src) measures and draws a formula: LaTeX sets it, dvisvgm turns it into paths. Results are cached
# in .texcache/; formulas not yet cached are collected while the figures are built, rendered in one
# LaTeX run, and the figures are built again.

TEX_CACHE = os.path.join(os.path.dirname(HERE), ".texcache")
TEX_PREAMBLE = r"""\documentclass{article}
\usepackage[T1]{fontenc}\usepackage{lmodern}\usepackage{inconsolata}
\usepackage[default]{sourcesanspro}\renewcommand{\familydefault}{\rmdefault}
\usepackage{amsmath,amssymb,stmaryrd,mathtools,xcolor,mathpartir}
\definecolor{ink}{HTML}{0f172a}\definecolor{muted}{HTML}{64748b}\definecolor{rulename}{HTML}{0073A3}
\definecolor{amber}{HTML}{b45309}\definecolor{kw}{HTML}{cf222e}\definecolor{const}{HTML}{0550ae}
\newcommand{\lean}[1]{\mathtt{#1}}
\newcommand{\Prop}{\lean{Prop}}\newcommand{\Sort}{\lean{Sort}}\newcommand{\Nat}{\lean{Nat}}
\newcommand{\Empty}{\lean{Empty}}\newcommand{\True}{\lean{True}}\newcommand{\False}{\lean{False}}
\newcommand{\intro}{\lean{True.intro}}\newcommand{\List}{\lean{List}}\newcommand{\Tree}{\lean{Tree}}
\newcommand{\fun}{\lean{fun}}\newcommand{\srt}[1]{\lean{Sort}\ #1}
\newcommand{\lam}[3]{\fun\ (#1 : #2) \mapsto #3}
\newcommand{\fa}[3]{\forall\,(#1 : #2),\ #3}
\newcommand{\den}[2][\rho]{\llbracket #2\rrbracket_{#1}}
\newcommand{\xv}{\rho,\,x\mapsto v}
\newcommand{\pv}{\operatorname{pv}}
\newcommand{\pt}{\bullet}
\newcommand{\ok}[2][\rho]{#2\ \checkmark\mkern-5mu{}_{#1}}
\newcommand{\imax}{\operatorname{imax}}
\newcommand{\rn}[1]{\textcolor{rulename}{\textsf{#1}}}\renewcommand{\TirNameStyle}[1]{#1}
\newcommand{\muted}[1]{\textcolor{muted}{#1}}
% two centred lines of premises (an \halign, since mathpartir takes \\ as a premise separator)
\protected\def\twolines#1#2{\vbox{\halign{\hfil$##$\hfil\cr #1\cr\noalign{\vskip 8pt} #2\cr}}}
\hoffset=-1in \voffset=-1in \parindent=0pt \textwidth=200cm
\newsavebox\fb\newsavebox\pb
\begin{document}
"""
_tex_missing = {}


def _tex_key(src, mode):
    return hashlib.sha1((TEX_PREAMBLE + mode + "\0" + src).encode()).hexdigest()[:16]


def _tex_render():
    """Render all formulas collected in _tex_missing in one LaTeX run, into the cache."""
    os.makedirs(TEX_CACHE, exist_ok=True)
    keys = list(_tex_missing)
    body = []
    for k in keys:
        src, mode = _tex_missing[k]
        box = "$" + src + "$" if mode == "math" else src
        body.append(r"\sbox\fb{" + box + r"}\typeout{TEXDIM:\the\wd\fb:\the\ht\fb:\the\dp\fb}"
                    r"\shipout\hbox{\usebox\fb}")
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "f.tex"), "w") as f:
            f.write(TEX_PREAMBLE + "\n".join(body) + "\n\\end{document}\n")
        r = subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", "f.tex"], cwd=d,
                           capture_output=True, text=True)
        log = open(os.path.join(d, "f.log"), errors="replace").read()
        if r.returncode != 0:
            err = log[log.find("\n!"):][:1500] if "\n!" in log else log[-1500:]
            raise SystemExit("LaTeX failed:\n" + err)
        dims = re.findall(r"TEXDIM:([\d.]+)pt:([\d.]+)pt:([\d.]+)pt", log)
        subprocess.run(["dvisvgm", "--no-fonts", "--fontmap=+SourceSansPro.map", "--page=1-", "-o", "p-%p.svg", "f.dvi"], cwd=d,
                       capture_output=True, check=True)
        width = len(str(len(keys)))
        for i, k in enumerate(keys):
            name = os.path.join(d, f"p-{i + 1:0{width}d}.svg")
            if not os.path.exists(name):
                name = os.path.join(d, f"p-{i + 1}.svg")
            svgsrc = open(name).read()
            inner = svgsrc[svgsrc.index(">", svgsrc.index("<svg")) + 1:svgsrc.rindex("</svg>")]
            inner = inner.replace("id='", f"id='t{k}-").replace("href='#", f"href='#t{k}-")
            pt = 72 / 72.27  # TeX points to big points (the SVG's unit)
            w, h, dp = (float(v) * pt for v in dims[i])
            with open(os.path.join(TEX_CACHE, k + ".json"), "w") as f:
                json.dump({"w": w, "h": h, "d": dp, "svg": inner.strip()}, f)
    _tex_missing.clear()


class Tex:
    """A typeset formula at a given size (the px size a 10pt font gets)."""

    def __init__(self, src, size=34, mode="math"):
        self.s = size / 10 * 72.27 / 72  # px per big point
        k = _tex_key(src, mode)
        try:
            with open(os.path.join(TEX_CACHE, k + ".json")) as f:
                c = json.load(f)
        except FileNotFoundError:
            _tex_missing[k] = (src, mode)
            c = {"w": 0, "h": 0, "d": 0, "svg": ""}
        self.svg = c["svg"]
        self.w, self.h, self.d = c["w"] * self.s, c["h"] * self.s, c["d"] * self.s

    def at(self, x, y, anchor="start", fill=INK, valign="baseline", extra=""):
        """The formula with its reference point at (x, y): anchor start/middle/end horizontally;
        valign baseline, top or middle vertically."""
        x -= {"start": 0, "middle": self.w / 2, "end": self.w}[anchor]
        y += {"baseline": 0, "top": self.h, "middle": (self.h - self.d) / 2}[valign]
        return (f'<g transform="translate({x:.2f} {y - self.h:.2f}) scale({self.s:.4f}) translate(72 72)" '
                f'fill="{fill}"{extra}>{self.svg}</g>')


def tex(x, y, src, anchor="start", size=34, fill=INK, mode="math", valign="baseline", extra=""):
    return Tex(src, size, mode).at(x, y, anchor, fill, valign, extra)


def sugar():
    out = []
    LX, LW, RX, RW = 40, 580, 780, 780
    out.append(text(LX + LW / 2, 40, "LEAN", size=22, weight=700, fill=MUTED, extra=' letter-spacing="2"'))
    out.append(text(RX + RW / 2, 40, "SET THEORY", size=22, weight=700, fill=MUTED, extra=' letter-spacing="2"'))

    kw = lambda s: f'<tspan fill="{KW}" font-weight="700">{escape(s)}</tspan>'
    cn = lambda s: f'<tspan fill="{CONST}">{escape(s)}</tspan>'
    pl = escape
    OR = r"\quad \muted{\text{or}} \quad "

    rows = [
        (cn("Nat"), r"\mathbb{N}"),
        (pl("α → β"), r"A \Longrightarrow B" + OR + "B^A"),
        (kw("∀") + pl(" (x : α), β x"), r"\forall x \in A.\ B(x)" + OR + r"\prod_{x \in A} B(x)"),
        (kw("fun") + pl(" (x : α) ↦ t"),
         [r"\text{Assume } A.\ \dots\ t" + OR + r"\text{Let } x \in A.\ \dots\ t",
          r"\muted{\text{or}} \quad x \in A \mapsto t"]),
        (kw("def") + pl(" c : α := v"), r"c \coloneqq v \quad \muted{\text{with}} \quad v \in A"),
        (kw("inductive") + pl(" T …"), r"T \coloneqq \{ \dots \} \quad \muted{\text{(but disjoint)}}"),
    ]
    top, gap, bh1, lh = 70, 22, 82, 54
    heights = [bh1 + lh * (len(m) - 1) if isinstance(m, list) else bh1 for _, m in rows]
    W, H = 1600, top + sum(heights) + gap * len(rows)
    y = top - gap - heights[0]
    for i, (lean, math) in enumerate(rows):
        y += (heights[i - 1] if i else heights[0]) + gap
        bh = heights[i]
        lines = math if isinstance(math, list) else [math]
        out.append(rect(LX, y, LW, bh, rx=12, fill=CODE_BG, stroke=CODE_LINE))
        out.append(f'<text x="{LX + LW / 2}" y="{y + bh / 2 + 12}" font-size="36" text-anchor="middle" '
                   f'font-family="{MONO}" fill="{INK}" xml:space="preserve">{lean}</text>')
        out.append(arrow(LX + LW + 30, y + bh / 2, RX - 30, y + bh / 2, color=TEAL, sw=4, head=18))
        out.append(rect(RX, y, RW, bh, rx=12, fill=BLUE_BG, stroke=BLUE_LINE))
        for k, line in enumerate(lines):
            ly = y + bh / 2 + (k - (len(lines) - 1) / 2) * lh
            out.append(tex(RX + RW / 2, ly, line, "middle", size=40, valign="middle"))
    return svg(W, H, "Lean syntax and its set-theoretic reading: Nat is ℕ, def c : α := v is c ≔ v with v ∈ A, arrows are implication or "
               "function spaces, ∀ is universal quantification or a dependent product, fun is x ↦ t, "
               "inductive is a set comprehension, but disjoint", out)


# ── History of Lean: timeline with a 2026 zoom ─────────────────────────

def history():
    W, H = 1600, 760
    AX = 330  # axis y
    # piecewise-linear time axis; 2026 (Jul–Nov) is zoomed in
    segs = [(2013.0, 60), (2020.0, 400), (2026.0, 960), (2026.5, 1030), (2026.92, 1580)]

    def X(t):
        for (t0, x0), (t1, x1) in zip(segs, segs[1:]):
            if t0 <= t <= t1:
                return x0 + (x1 - x0) * (t - t0) / (t1 - t0)
        raise ValueError(t)

    out = []
    # zoom background
    out.append(rect(1010, 20, 590, 720, rx=16, fill="#f8fafc", stroke=CODE_LINE))
    out.append(text(1305, 58, "2026", size=30, weight=700, fill=MUTED))
    # axis
    out.append(f'<line x1="{X(2013)}" y1="{AX}" x2="{X(2026.0)}" y2="{AX}" stroke="{LINE}" stroke-width="4"/>')
    out.append(f'<line x1="{X(2026.5)}" y1="{AX}" x2="{X(2026.92)}" y2="{AX}" stroke="{LINE}" stroke-width="4"/>')
    out.append(text(995, AX + 10, "⋯", size=34, fill=LINE))
    for y in range(2013, 2027):
        x = X(y)
        out.append(f'<line x1="{x}" y1="{AX - 8}" x2="{x}" y2="{AX + 8}" stroke="{LINE}" stroke-width="3"/>')
        if y % 2 == 1 or y >= 2020:
            out.append(text(x, AX + 36, str(y) if y < 2026 else "", size=22, fill=MUTED))
    for t, lab in [(2026.5, "Jul"), (2026.583, "Aug"), (2026.667, "Sep"), (2026.75, "Oct"), (2026.833, "Nov")]:
        x = X(t)
        out.append(f'<line x1="{x}" y1="{AX - 8}" x2="{x}" y2="{AX + 8}" stroke="{LINE}" stroke-width="3"/>')
        out.append(text(x, AX + 36, lab, size=22, fill=MUTED))

    # lane labels
    out.append(text(60, 70, "LEAN", size=20, weight=700, fill=BLUE, anchor="start", extra=' letter-spacing="2"'))
    out.append(text(60, 420, "MATHEMATICS", size=20, weight=700, fill=TEAL, anchor="start", extra=' letter-spacing="2"'))
    out.append(text(60, 610, "AI", size=20, weight=700, fill="#7c3aed", anchor="start", extra=' letter-spacing="2"'))

    def event(t, y, title, sub=None, color=BLUE, anchor="middle", t2=None, strong=False):
        x = X(t)
        if t2 is not None:  # a span on the axis
            x2 = X(t2)
            out.append(f'<rect x="{x}" y="{AX - 7}" width="{x2 - x}" height="14" rx="7" fill="{color}"/>')
            lx = (x + x2) / 2
        else:
            out.append(f'<circle cx="{x}" cy="{AX}" r="9" fill="{color}"/>')
            lx = x
        top = y - 30 if y < AX else y - 30
        out.append(f'<line x1="{lx}" y1="{AX + (-9 if y < AX else 9)}" x2="{lx}" y2="{y + (12 if y < AX else -30)}" '
                   f'stroke="{color}" stroke-width="2"/>')
        tx = lx + (8 if anchor == "start" else -8 if anchor == "end" else 0)
        out.append(text(tx, y if y < AX else y + 2, escape(title), size=26 if not strong else 28,
                        weight=700 if strong else 600, fill=color, anchor=anchor))
        if sub:
            out.append(text(tx, (y if y < AX else y + 2) + 28, escape(sub), size=21, fill=MUTED, anchor=anchor))

    # Lean
    event(2013.5, 240, "Lean", "Leonardo de Moura, MSR", anchor="start")
    event(2017.5, 150, "Lean 3, Mathlib", anchor="middle")
    event(2021.0, 240, "Lean 4", anchor="middle")
    event(2023.6, 150, "Lean FRO", "Mathlib in Lean 4", anchor="middle")

    # Mathematics
    event(2020.95, 430, "Liquid Tensor Experiment", "Scholze · Commelin (Freiburg)", color=TEAL,
          t2=2022.55, anchor="middle", strong=True)
    event(2023.9, 520, "PFR", "Tao et al.", color=TEAL, anchor="middle")
    event(2024.8, 430, "FLT project", "Buzzard", color=TEAL, anchor="middle")

    # AI (2024–2025)
    VIO = "#7c3aed"
    event(2024.55, 640, "AlphaProof", "IMO silver", color=VIO, anchor="end")
    event(2025.55, 560, "Aristotle", "IMO gold", color=VIO, anchor="end")
    event(2025.7, 680, "Strong PNT", "Math Inc", color=VIO, anchor="middle")

    # 2026 zoom (AI)
    event(2026.672, 130, "FLT", "Anthropic · 13M+ lines", color=VIO, anchor="end")
    event(2026.686, 240, "Navier–Stokes", "OpenAI; Buckmaster–Alpöge", color=VIO, anchor="start")
    event(2026.763, 430, "openai/math", "OpenAI · 721 papers, ~42% in Lean", color=VIO, anchor="end")
    event(2026.82, 560, "CFSG", "Axiom · 43.1M lines", color=VIO, anchor="end")
    event(2026.843, 680, "Stacks", "Axiom", color=VIO, anchor="end")
    return svg(W, H, "History of Lean, 2013 to 2026, with Lean releases, mathematics projects and AI results", out)


# ── Architecture: big Lean box, small kernel, export to external checkers ─

def architecture():
    W, H = 1600, 760
    out = []
    # The big box
    LX, LY, LW, LH = 10, 10, 900, 740
    out.append(rect(LX, LY, LW, LH, rx=20, fill="#ffffff", stroke=LINE, sw=3))
    out.append(text(LX + 30, LY + 58, "Lean", size=44, weight=700, fill=INK, anchor="start"))
    comps = [
        ["Parser", "Macros", "Elaborator"],
        ["Type classes", "Unifier", "Tactics"],
        ["simp", "grind", "Metaprograms"],
        ["Language server", "Infoview", "Compiler"],
        ["Lake", "…", None],
    ]
    bw, bh, gx, gy = 260, 90, 30, 34
    x0, y0 = LX + 35, LY + 100
    kernel = None
    for r, row in enumerate(comps):
        for c, name in enumerate(row):
            x, y = x0 + c * (bw + gx), y0 + r * (bh + gy)
            if name is None:
                kernel = (x, y)
                continue
            out.append(rect(x, y, bw, bh, rx=10, fill=CODE_BG, stroke="#cbd5e1"))
            out.append(text(x + bw / 2, y + bh / 2 + 10, escape(name), size=28, fill=INK))
    # The small, trusted kernel
    kx, ky = kernel
    kw_, kh = bw, bh
    out.append(rect(kx, ky, kw_, kh, rx=10, fill=BLUE_BG, stroke=BLUE_LINE, sw=2))
    out.append(text(kx + kw_ / 2, ky + kh / 2 + 2, "Kernel", size=30, weight=600, fill=INK))
    # rough sizes (lines in the lean4 repository, May 2026: src/kernel ~8k; Lean, Init, Std, Lake and C++ ~730k)
    out.append(text(kx + kw_ - 12, ky + kh - 10, "&lt; 10k LOC", size=18, fill=MUTED, anchor="end"))
    out.append(text(LX + LW - 24, LY + LH - 20, "≈ 700k LOC", size=24, fill=MUTED, anchor="end"))

    # proof export → Comparator
    CX, CW, CH = 1010, 210, 90
    CY = 330
    sx, sy = kx + kw_, ky + kh / 2
    out.append(f'<path d="M{sx} {sy} H{LX + LW + 25} V{CY + CH / 2} H{CX - 14}" fill="none" '
               f'stroke="{TEAL}" stroke-width="4"/>')
    out.append(f'<polygon points="{CX},{CY + CH / 2} {CX - 18},{CY + CH / 2 - 10} {CX - 18},{CY + CH / 2 + 10}" fill="{TEAL}"/>')
    out.append(text(LX + LW + 35, CY + CH / 2 + 50, "proof", size=24, weight=600, fill="#0e7490", anchor="start"))
    out.append(text(LX + LW + 35, CY + CH / 2 + 78, "export", size=24, weight=600, fill="#0e7490", anchor="start"))
    out.append(rect(CX, CY, CW, CH, rx=12, fill=BLUE_BG, stroke=BLUE_LINE, sw=2))
    out.append(text(CX + CW / 2, CY + CH / 2 + 10, "Comparator", size=30, weight=600, fill=INK))

    # External checkers
    checkers = [
        ("leanchecker", "C++"),
        ("nanoda", "Rust"),
        ("lean4lean", "Lean"),
        ("con-leche", "Lean · verified"),
        ("con-ron", "Rust · verified"),
        ("con-agua", "x86 · verified"),
    ]
    KX, KW, KH, KG = 1300, 290, 88, 32
    ky0 = H / 2 - (len(checkers) * KH + (len(checkers) - 1) * KG) / 2
    for i, (name, sub) in enumerate(checkers):
        y = ky0 + i * (KH + KG)
        out.append(f'<path d="M{CX + CW} {CY + CH / 2} C {CX + CW + 40} {CY + CH / 2} {KX - 50} {y + KH / 2} {KX - 12} {y + KH / 2}" '
                   f'fill="none" stroke="{LINE}" stroke-width="2.5"/>')
        out.append(f'<polygon points="{KX},{y + KH / 2} {KX - 14},{y + KH / 2 - 7} {KX - 14},{y + KH / 2 + 7}" fill="{LINE}"/>')
        out.append(rect(KX, y, KW, KH, rx=10, fill=BLUE_BG, stroke=BLUE_LINE, sw=2))
        out.append(text(KX + KW / 2, y + 38, escape(name), size=28, weight=600, fill=INK))
        out.append(text(KX + KW / 2, y + 70, escape(sub), size=21, fill=MUTED))
    return svg(W, H, "Architecture of Lean: many components and a small trusted kernel; proof export to "
               "Comparator and the external checkers leanchecker, nanoda, lean4lean, con-leche, con-ron, con-agua", out)


# ── Threat models: honest vs. malicious, xkcd style ──────────────────────

XKCD = "'xkcd Script', 'Comic Neue', 'Comic Sans MS', cursive"


def _wobble(rng, pts, amp=2.5, closed=False):
    """A hand-drawn path through the points: each segment gets a slight random bend."""
    if closed:
        pts = pts + [pts[0]]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        ln = max((dx * dx + dy * dy) ** 0.5, 1)
        off = rng.uniform(-amp, amp)
        d += f" Q{mx - dy / ln * off:.1f} {my + dx / ln * off:.1f} {x2:.1f} {y2:.1f}"
    return d


def _stroke(d, sw=4, fill="none"):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def _circle(rng, cx, cy, r, n=14):
    import math
    pts = [(cx + r * math.cos(2 * math.pi * i / n) * rng.uniform(0.97, 1.03),
            cy + r * math.sin(2 * math.pi * i / n) * rng.uniform(0.97, 1.03)) for i in range(n)]
    return _wobble(rng, pts, amp=1.0, closed=True)


def _panel(ox, honest, rng):
    out = []
    # whiteboard on a stand
    bx0, by0, bx1, by1 = ox + 250, 90, ox + 740, 530
    out.append(f'<path d="{_wobble(rng, [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], closed=True)}" '
               f'fill="#ffffff" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    out.append(_stroke(_wobble(rng, [(bx0 + 40, by1), (bx0 + 20, 680)])))
    out.append(_stroke(_wobble(rng, [(bx1 - 40, by1), (bx1 - 20, 680)])))
    # formula
    rel = "=" if honest else "≠"
    sup = lambda s: f'<tspan font-size="40" dy="-24">{s}</tspan><tspan dy="24"> </tspan>'
    out.append(f'<text x="{(bx0 + bx1) / 2}" y="180" font-size="66" text-anchor="middle" font-family="{XKCD}" '
               f'fill="{INK}" xml:space="preserve">a{sup("2")}+ b{sup("2")}{rel} c{sup("2")}</text>')
    # triangle: right angle at A
    A, B, C = (ox + 340, 470), (ox + 650, 470), (ox + 340, 250)
    if honest:
        tri = _wobble(rng, [A, B, C], amp=1.5, closed=True)
    else:
        # the sides are not quite straight
        dx, dy = C[0] - B[0], C[1] - B[1]
        ln = (dx * dx + dy * dy) ** 0.5
        nx, ny = -dy / ln * 28, dx / ln * 28  # perpendicular, away from A
        tri = (f"M{A[0]} {A[1]} Q{(A[0] + B[0]) / 2} {A[1] + 18} {B[0]} {B[1]} "
               f"Q{(B[0] + C[0]) / 2 + nx:.1f} {(B[1] + C[1]) / 2 + ny:.1f} {C[0]} {C[1]} "
               f"Q{A[0] - 16} {(A[1] + C[1]) / 2} {A[0]} {A[1]}")
    out.append(_stroke(tri, sw=4))
    out.append(_stroke(f"M{A[0]} {A[1] - 28} H{A[0] + 28} V{A[1]}", sw=3))
    lab = lambda x, y, s: f'<text x="{x}" y="{y}" font-size="44" text-anchor="middle" font-family="{XKCD}" fill="{INK}">{s}</text>'
    out.append(lab(A[0] - 30 - (14 if not honest else 0), (A[1] + C[1]) / 2 + 14, "a"))
    out.append(lab((A[0] + B[0]) / 2, A[1] + 46 + (14 if not honest else 0), "b"))
    out.append(lab((B[0] + C[0]) / 2 + 30 + (22 if not honest else 0), (B[1] + C[1]) / 2 - 10 - (14 if not honest else 0), "c"))
    # stick figure, facing the board, writing
    hx, hy = ox + 160, 330
    out.append(_stroke(_circle(rng, hx, hy, 34)))
    out.append(_stroke(_wobble(rng, [(hx, hy + 34), (hx + 4, hy + 180)])))               # body
    out.append(_stroke(_wobble(rng, [(hx + 4, hy + 180), (hx - 30, hy + 320)])))         # legs
    out.append(_stroke(_wobble(rng, [(hx + 4, hy + 180), (hx + 42, hy + 320)])))
    out.append(_stroke(_wobble(rng, [(hx + 2, hy + 75), (hx + 55, hy + 45), (bx0 + 60, 250)])))  # writing arm
    out.append(_stroke(_wobble(rng, [(hx + 2, hy + 75), (hx - 26, hy + 150)])))          # other arm
    out.append(_stroke(f"M{bx0 + 60} 250 l 14 -16", sw=7))                                # marker
    if not honest:
        # Black Hat's hat: a rounded crown on a short brim, sitting low on the head
        crown = (f"M{hx - 25} {hy - 20} L{hx - 22} {hy - 54} Q{hx - 21} {hy - 62} {hx - 12} {hy - 62} "
                 f"L{hx + 12} {hy - 62} Q{hx + 21} {hy - 62} {hx + 22} {hy - 54} L{hx + 25} {hy - 20} Z")
        out.append(f'<path d="{crown}" fill="{INK}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
        out.append(_stroke(f"M{hx - 36} {hy - 20} L{hx + 36} {hy - 20}", sw=8))
    return out


def threat_models():
    import random
    rng = random.Random(4)
    W, H = 1600, 760
    out = []
    out.append(text(400, 46, "Honest attempt", size=40, weight=600, fill=INK))
    out.append(text(1240, 46, "Malicious attempt", size=40, weight=600, fill=INK))
    out += _panel(20, True, rng)
    out += _panel(840, False, rng)
    return svg(W, H, "Threat models: an honest stick figure writes a² + b² = c² next to a right triangle; "
               "a stick figure with a black hat writes a² + b² ≠ c² next to a triangle whose sides are not quite straight", out)


# ── Attacks and defenses, from superficial to deep ───────────────────────

def attacks():
    rows = [
        ("Wrong definitions or statement", "Human review, Formal Conjectures"),
        ("Swapped statement", "Comparator"),
        ("Malicious (meta)code", "Sandboxes"),
        ("Kernel implementation bug", "Code review, verified implementation"),
        ("Kernel compiler or runtime bug", "Multiple kernels"),
        ("Lean’s type theory inconsistent", "Relative consistency proof"),
        ("Set theory inconsistent", "🤷"),
    ]
    out = []
    LX, LW, RX, RW = 60, 600, 800, 740
    out.append(text(LX + LW / 2, 40, "ATTACK", size=22, weight=700, fill=MUTED, extra=' letter-spacing="2"'))
    out.append(text(RX + RW / 2, 40, "DEFENSE", size=22, weight=700, fill=MUTED, extra=' letter-spacing="2"'))
    top, rh, bh = 70, 92, 74
    W, H = 1600, top + len(rows) * rh
    for i, (att, dfn) in enumerate(rows):
        y = top + i * rh
        out.append(rect(LX, y, LW, bh, rx=12, fill=RED_BG, stroke="#fca5a5"))
        out.append(text(LX + LW / 2, y + bh / 2 + 11, escape(att), size=31, weight=500))
        out.append(arrow(LX + LW + 30, y + bh / 2, RX - 30, y + bh / 2, color=TEAL, sw=4, head=18))
        out.append(rect(RX, y, RW, bh, rx=12, fill=BLUE_BG, stroke=BLUE_LINE))
        if dfn == "🤷":
            out.append(text(RX + RW / 2, y + bh / 2 + 16, dfn, size=48,
                            extra=" font-family=\"'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif\""))
        else:
            out.append(text(RX + RW / 2, y + bh / 2 + 11, escape(dfn), size=31, weight=500))
    return svg(W, H, "Attacks and defenses: " + "; ".join(f"{a}: {d}" for a, d in rows), out)


# ── Comparator: challenge + solution in, two verdicts out ────────────────

EMOJI = "'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif"


def _file(x, y, w, h, name, lines=()):
    f = 30  # folded corner
    out = [
        f'<path d="M{x} {y} H{x + w - f} L{x + w} {y + f} V{y + h} H{x} Z" fill="#ffffff" '
        f'stroke="{LINE}" stroke-width="3" stroke-linejoin="round"/>',
        f'<path d="M{x + w - f} {y} V{y + f} H{x + w}" fill="none" stroke="{LINE}" stroke-width="3" '
        f'stroke-linejoin="round"/>',
        text(x + w / 2, y + h - 22, escape(name), size=24, weight=600, mono=True, fill=INK),
    ]
    for i, runs in enumerate(lines):
        spans = "".join(f'<tspan fill="{c}" font-weight="{wt}">{escape(t)}</tspan>' for t, c, wt in runs)
        out.append(f'<text x="{x + 18}" y="{y + 62 + i * 34}" font-size="21" font-family="{MONO}" '
                   f'fill="{INK}" xml:space="preserve">{spans}</text>')
    return out


def _check(cx, cy, r=24):
    return [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GREEN}"/>',
            f'<path d="M{cx - r * 0.45} {cy + r * 0.02} L{cx - r * 0.1} {cy + r * 0.38} L{cx + r * 0.5} {cy - r * 0.35}" '
            f'fill="none" stroke="#ffffff" stroke-width="{r * 0.22:.1f}" stroke-linecap="round" stroke-linejoin="round"/>']


def _verdict(x, y, w, h, label):
    out = [rect(x, y, w, h, rx=14, fill=GREEN_BG, stroke=GREEN, sw=2.5)]
    out += _check(x + 48, y + h / 2)
    out.append(text(x + 90, y + h / 2 + 11, escape(label), size=32, weight=600, fill=GREEN, anchor="start"))
    return out


def comparator():
    W, H = 1600, 740
    out = []
    head = [("theorem", KW, 700), (" t : P :=", INK, 400)]
    # inputs, symmetric about the centre line x = 800
    FW, FH, fy = 260, 190, 30
    chx, sox = 800 - 250 - FW // 2, 800 + 250 - FW // 2
    out += _file(chx, fy, FW, FH, "Challenge.lean", [head, [("  sorry", KW, 700)]])
    out += _file(sox, fy, FW, FH, "Solution.lean", [head, [("  ⋯", INK, 700)]])
    out.append(text(chx - 80, fy + FH / 2 + 30, "🧑‍🏫", size=90, extra=f' font-family="{EMOJI}"'))
    out.append(text(sox + FW + 80, fy + FH / 2 + 30, "🤖", size=90, extra=f' font-family="{EMOJI}"'))
    # the solution and its author run in a sandbox
    out.append(rect(sox - 22, fy - 20, FW + 175, FH + 50, rx=16, fill="none", stroke=MUTED, sw=2.5,
                    extra=' stroke-dasharray="10 7"'))
    out.append(text(sox + FW + 140, fy + FH + 18, "SANDBOX", size=20, weight=700, fill=MUTED, anchor="end",
                    extra=' letter-spacing="2"'))
    # Comparator, in the centre
    CW, CH = 350, 100
    CX, CY = 800 - CW / 2, 320
    out.append(arrow(chx + FW / 2, fy + FH + 6, CX + 110, CY - 6, color=LINE, sw=3.5, head=16))
    out.append(arrow(sox + FW / 2, fy + FH + 6, CX + CW - 110, CY - 6, color=LINE, sw=3.5, head=16))
    out.append(rect(CX, CY, CW, CH, rx=14, fill=BLUE_BG, stroke=BLUE_LINE, sw=2.5))
    out.append(text(800, CY + CH / 2 + 12, "Comparator", size=36, weight=700, fill=INK))
    # the two verdicts, in the lower corners
    vw, vh, vy = 400, 96, 610
    lx, rx = 800 - 440 - vw / 2, 800 + 440 - vw / 2
    a0 = (CX + 60, CY + CH + 6)
    a1 = (CX + CW - 60, CY + CH + 6)
    l_end = (lx + vw / 2 + 60, vy - 6)
    r_end = (rx + vw / 2 - 60, vy - 6)
    out.append(arrow(*a0, *l_end, color=TEAL, sw=4, head=18))
    out.append(arrow(*a1, *r_end, color=TEAL, sw=4, head=18))
    out += _verdict(lx, vy, vw, vh, "Same statement")
    out += _verdict(rx, vy, vw, vh, "Solution valid")
    # the checkers, bracketed, pointing onto the arrow to "Solution valid"
    checkers = ["leanchecker", "nanoda", "lean4lean", "con-leche", "con-ron"]
    BX, BW, BH, BG, ky0 = 1330, 230, 42, 10, 300
    for n, name in enumerate(checkers):
        y = ky0 + n * (BH + BG)
        out.append(rect(BX, y, BW, BH, rx=8, fill=BLUE_BG, stroke=BLUE_LINE, sw=1.5))
        out.append(text(BX + BW / 2, y + BH / 2 + 8, escape(name), size=22, weight=500, fill=INK))
    top, bot = ky0, ky0 + len(checkers) * (BH + BG) - BG
    bx = BX - 18
    out.append(f'<path d="M{bx + 10} {top} H{bx} V{bot} H{bx + 10}" fill="none" stroke="{LINE}" stroke-width="2.5"/>')
    mid = ((a1[0] + r_end[0]) / 2, (a1[1] + r_end[1]) / 2)
    out.append(arrow(bx, (top + bot) / 2, mid[0] + 14, mid[1] - 8, color=LINE, sw=2.5, head=13))
    return svg(W, H, "Comparator: an author writes Challenge.lean, an AI writes Solution.lean in a sandbox; Comparator "
               "checks that they state the same theorem and, using five checkers, that the solution is valid", out)


# ── A Lean checker is a type checker: declarations and a checklist ───────

def _checkbox(x, y, s=34, checked=True):
    out = [rect(x, y, s, s, rx=6, fill="#ffffff", stroke=GREEN if checked else LINE, sw=3)]
    if checked:
        out.append(f'<path d="M{x + s * 0.22} {y + s * 0.52} L{x + s * 0.43} {y + s * 0.74} L{x + s * 0.8} {y + s * 0.28}" '
                   f'fill="none" stroke="{GREEN}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>')
    return out


def checker():
    VIO = "#7c3aed"
    AMB = "#d97706"
    out = []
    kw = lambda s: (s, KW, 700)
    pl = lambda s: (s, INK, 400)
    # left: the declarations, each with a coloured bar
    decls = [
        (BLUE, [[kw("def"), pl(" f : T :=")], [pl("  t")]]),
        (AMB, [[kw("theorem"), pl(" thm : P :=")], [pl("  p")]]),
        (VIO, [[kw("inductive"), pl(" I "), kw("where")], [pl("  | c : A → I")]]),
    ]
    CX, CY, CW = 40, 60, 640
    size, lh = 34, 52
    nlines = sum(len(l) for _, l in decls) + len(decls) - 1
    CH = nlines * lh + 50
    out.append(rect(CX, CY, CW, CH, rx=10, fill=CODE_BG, stroke=CODE_LINE))
    y = CY + 25
    baselines = []
    for color, lines in decls:
        for runs in lines:
            spans = "".join(f'<tspan fill="{c}" font-weight="{wt}">{escape(t)}</tspan>' for t, c, wt in runs)
            baselines.append(y + 38)
            out.append(f'<text x="{CX + 44}" y="{y + 38}" font-size="{size}" font-family="{MONO}" '
                       f'fill="{INK}" xml:space="preserve">{spans}</text>')
            y += lh
        y += lh

    # right: the checklist
    ctx = r"\emptyset \vdash "
    items = [
        (None, "All names defined"),
        (None, "Declarations acyclic"),
        ((0, 9), "M" + ctx + r"T \Rightarrow \srt{u}"),
        ((1, 3), "M" + ctx + r"t \Rightarrow T', \quad " + ctx + r"T' \equiv T"),
        ((2, 15), "M" + ctx + r"P \Rightarrow \Prop"),
        ((3, 3), "M" + ctx + r"p \Rightarrow P', \quad " + ctx + r"P' \equiv P"),
        ((5, 13), "Positivity"),
        (None, "…"),
    ]
    RX, ry, rlh = 790, 40, 76
    for color, label in items:
        out += _checkbox(RX + 4, ry + 8)
        if color:  # an arrow to the token on the left, ending in the gap below its line
            line, col = color
            tx, ty = CX + 44 + col * size * 0.6 + 4, baselines[line] + 12
            sx, sy = RX - 14, ry + 25
            out.append(f'<path d="M{sx} {sy} C {sx - 120} {sy} {tx + 120} {ty} {tx + 12} {ty}" fill="none" '
                       f'stroke="{LINE}" stroke-width="2.5"/>')
            out.append(f'<polygon points="{tx},{ty} {tx + 14},{ty - 6} {tx + 14},{ty + 6}" fill="{LINE}"/>')
        if label.startswith("M"):
            out.append(tex(RX + 62, ry + 38, label[1:], size=40))
        else:
            out.append(f'<text x="{RX + 62}" y="{ry + 38}" font-size="36" fill="{INK}" '
                       f'xml:space="preserve">{label}</text>')
        ry += rlh
    W, H = 1600, max(CY + CH, ry) + 20
    return svg(W, H, "A Lean checker is a type checker: for def f : T := t, theorem thm : P := p and an inductive "
               "type I it checks that all names are defined, declarations are acyclic, T is a sort, t has a type "
               "definitionally equal to T, P is a proposition, p has a type definitionally equal to P, "
               "positivity, and more", out)


# ── The three judgments ─────────────────────────────────────────────────

def judgments():
    rows = [
        (r"\Gamma \vdash t \Rightarrow T", r"expression $t$ has type $T$"),
        (r"\Gamma \vdash t \leadsto t'", r"expression $t$ reduces to $t'$"),
        (r"\Gamma \vdash s \equiv t", r"expressions $s$ and $t$ are definitionally equal"),
    ]
    out = []
    JX, PX = 110, 640
    out.append(tex(PX, 60, r"\textsf{In context $\Gamma$, \dots}", size=40, fill=MUTED, mode="text"))
    top, rh = 110, 130
    for i, (j, prose) in enumerate(rows):
        y = top + i * rh
        out.append(rect(JX - 30, y, 470, 96, rx=12, fill=BLUE_BG, stroke=BLUE_LINE))
        out.append(tex(JX, y + 48, j, size=56, valign="middle"))
        out.append(tex(PX, y + 62, r"\textsf{\dots\ " + prose + "}", size=40, mode="text"))
    W, H = 1600, top + len(rows) * rh
    return svg(W, H, "Three judgments: in context Γ, expression t has type T; t reduces to t′; "
               "s and t are definitionally equal", out)


# ── Typing rules: Var, Lam, App ──────────────────────────────────────────

def _rule(cx, y, premises, conclusion, name, size=44):
    """An inference rule, centred at cx with its top at y, its name to the right of the bar."""
    prem = r" \and ".join(premises or [r"\ "])
    src = r"\inferrule*[right=\rn{" + name + "}]{" + prem + "}{" + conclusion + "}"
    return [tex(cx, y, src, "middle", size=size, valign="top")]


def typing_rules():
    # The checker's rules, as in the con-leche proof idea, Sec. 2.3: inference (var, pi, lam, app),
    # reduction (beta) and definitional equality (refl, red-l, proof-irrel).
    G = r"\Gamma \vdash "
    z = 36
    out = []
    out += _rule(250, 20, [r"(x : A) \in \Gamma"], G + r"x \Rightarrow A", "var", size=z)
    out += _rule(1030, 20, [G + r"A \Rightarrow S \leadsto \srt{u}",
                            r"\Gamma,\, x : A \vdash B \Rightarrow T \leadsto \srt{v}"],
                 G + r"\fa{x}{A}{B} \Rightarrow \srt{(\imax(u, v))}", "pi", size=z)
    out += _rule(800, 170, [G + r"A \Rightarrow S \leadsto \srt{u}", r"\Gamma,\, x : A \vdash b \Rightarrow B"],
                 G + r"\lam{x}{A}{b} \Rightarrow \fa{x}{A}{B}", "lam", size=z)
    out += _rule(800, 320, [G + r"f \Rightarrow T \leadsto \fa{x}{A}{B}", G + r"a \Rightarrow C", G + r"C \equiv A"],
                 G + r"f\;a \Rightarrow B[x \coloneqq a]", "app", size=z)
    out += _rule(150, 470, [], G + r"a \equiv a", "refl", size=z)
    out += _rule(530, 470, [G + r"a \leadsto a'", G + r"a' \equiv b"], G + r"a \equiv b", "red-l", size=z)
    # con-leche's proof irrelevance: both sides are proofs; their types are not compared
    out += _rule(1250, 470, [G + r"a \Rightarrow A \Rightarrow \Prop", G + r"b \Rightarrow B \Rightarrow \Prop"],
                 G + r"a \equiv b", "proof-irrel", size=z)
    out += _rule(800, 620, [], G + r"(\lam{x}{A}{b})\;a \leadsto b[x \coloneqq a]", "beta", size=z)
    return svg(1660, 740, "Rules of the checker: var, pi, lam, app for inference; beta for reduction; "
               "refl, red-l and proof irrelevance for definitional equality", out)


# ── Statements of the standard path, shown in the hover pop-ups ────────────

def statements():
    G = r"\Gamma \vdash "
    rows = [
        ("Weakening", [r"If $\Gamma, \Gamma' \vdash t \Rightarrow T$, then $\Gamma, \Delta, \Gamma' \vdash t \Rightarrow T$."]),
        ("Substitution", [r"If $\Gamma,\, x : A \vdash b \Rightarrow B$, $" + G + r"a \Rightarrow C$ and $" + G
                          + r"C \equiv A$,",
                          r"then $" + G + r"b[x \coloneqq a] \Rightarrow B'$ with $" + G
                          + r"B' \equiv B[x \coloneqq a]$."]),
        ("Transitive ≡", [r"If $" + G + r"s \equiv t$ and $" + G + r"t \equiv u$, then $" + G + r"s \equiv u$."]),
        ("∀-injectivity", [r"If $" + G + r"\fa{x}{A}{B} \equiv \fa{x}{A'}{B'}$, then $" + G
                           + r"A \equiv A'$ and $\Gamma,\, x : A \vdash B \equiv B'$."]),
        ("Subject reduction", [r"If $" + G + r"t \Rightarrow T$ and $" + G + r"t \leadsto t'$, then $" + G
                               + r"t' \Rightarrow T'$ with $" + G + r"T' \equiv T$."]),
        ("Normalization", [r"If $" + G + r"t \Rightarrow T$, then every reduction sequence from $t$ is finite."]),
        ("Canonicity", [r"If $\emptyset \vdash t \Rightarrow T$, $T$ is an inductive type and $t$ is normal, "
                        r"then $t$ starts with a constructor."]),
        ("Consistency", [r"There is no $t$ with $\emptyset \vdash t \Rightarrow T$ and $\emptyset \vdash T \equiv \False$."]),
    ]
    return rows

# ── Standard path to consistency: theory vs. Lean ───────────────────────

# lean4lean's ∀-injectivity, still resting on a `sorry` (the const case of LR.adequacy) as of Nov 2026
FORALL_INV = ("https://github.com/digama0/lean4lean/blob/67f63b0c818920dfaed2ad07ccff187a6a8fe1e3/"
              "Lean4Lean/Experimental/ShapeLogRelAdequacy.lean#L450")


def standard_path():
    AMB = "#b45309"
    # (property, status now, note, status soon) -- "soon" is after the kernel renovation (lean4#14977)
    rows = [
        ("Weakening, substitution", "ok", "", None),
        ("Transitive ≡", "fails", "Acc, quotients of Prop", "ok"),
        ("∀-injectivity", "open", ("open conjecture (actively worked on)", FORALL_INV), None),
        ("Subject reduction", "fails", "since ≡ is not transitive", "ok"),
        ("Normalization", "fails", "propext + proof irrelevance", None),
        ("Canonicity", "fails", "axioms block reduction", None),
        ("Consistency", "open", "not via this path", None),
    ]

    def mark(x, y, status):
        if status == "ok":
            return _check(x, y - 11, r=18)
        if status == "fails":
            return [f'<circle cx="{x}" cy="{y - 11}" r="18" fill="{RED}"/>'
                    f'<path d="M{x - 7} {y - 18} L{x + 7} {y - 4} M{x + 7} {y - 18} L{x - 7} {y - 4}" '
                    f'stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>']
        return [text(x, y + 2, "?", size=40, weight=700, fill=AMB)]

    st = dict(statements())
    c = lambda v: (escape(v), "code")
    examples = {
        # Carneiro, The Type Theory of Lean, §3.1.1 (quotients of propositions)
        "Transitive ≡": [c("-- p : Prop,  h : p,  q : Quot r  (r a relation on p)"),
                         c("Quot.lift f H q ≡ Quot.lift f H (Quot.mk r h) ≡ f h"),
                         c("Quot.lift f H q ≢ f h")],
        # Carneiro, The Type Theory of Lean, §3.1.2
        "Subject reduction": [(r"Given $\alpha \equiv \beta$, $\beta \equiv \gamma$, $\alpha \not\equiv \gamma$ "
                               r"and $e : \gamma$:", "math"),
                              c("@id α (@id β e) : α      -- checks"),
                              c("  ⇝ @id α e              -- does not check")],
        # Abel & Coquand, LMCS 2020, in Lean 4 (only axiom: propext)
        "Normalization": [c("theorem tautext {A B : Prop} (a : A) (b : B) : A = B := propext ⟨fun _ => b, fun _ => a⟩"),
                          c("def T : Prop := ∀ A : Prop, A → A"),
                          c("def δ (z : T) : T := z (T → T) id z"),
                          c("def ω : T := fun A a => cast (tautext id a) δ"),
                          c("def Ω : T := δ ω            -- Ω ⇝ ω (T → T) id ω ⇝ δ ω ⇝ …")],
        "Canonicity": [c("Eq.rec (motive := fun _ _ => Nat) 5"),
                       c("  (propext ⟨fun _ => rfl, fun _ => trivial⟩ : True = (0 = 0)) : Nat"),
                       ("closed, normal, and not a numeral", "math")],
    }
    # Which statements a row's pop-up shows.
    pops = {"Weakening, substitution": ["Weakening", "Substitution"]}
    out, hits, popups, css = [], [], [], []
    TX, PX, SX, top, rh = 40, 560, 1450, 40, 76
    hdr = lambda x, s, a="start": text(x, top, s, size=22, weight=700, fill=MUTED, anchor=a, extra=' letter-spacing="2"')
    out += [hdr(TX, "IN THEORY"), hdr(PX, "IN PRACTICE"), hdr(SX, "AFTER lean4#14977", "middle")]
    y = top + 70
    for k, (name, now, note, soon) in enumerate(rows):
        out.append(f'<line x1="{TX}" y1="{y + 26}" x2="1560" y2="{y + 26}" stroke="{CODE_LINE}" stroke-width="1.5"/>')
        out.append(text(TX, y, escape(name), size=34, weight=600, fill=INK, anchor="start"))
        H = top + 70 + (len(rows) - 1) * rh + 46  # height of the figure

        def popup(pid, hx, hw, lines):
            # an invisible hover area and a pop-up box shown while it is hovered
            hits.append(f'<rect id="sp-hit-{pid}" x="{hx}" y="{y - 40}" width="{hw}" height="{rh - 4}" '
                       f'fill="transparent" style="cursor: help"/>')
            ph = 30 + 44 * len(lines)
            py = y + 34 if y + 34 + ph < H else y - 46 - ph
            pop = [rect(TX + 120, py, 1420, ph, rx=12, fill="#ffffff", stroke=BLUE_LINE, sw=2,
                        extra=' filter="drop-shadow(0 6px 12px rgba(15,23,42,0.18))"')]
            for m, (l, kind) in enumerate(lines):
                if kind == "code":
                    pop.append(f'<text x="{TX + 150}" y="{py + 48 + 44 * m}" font-size="24" font-family="{MONO}" '
                               f'fill="{INK}" xml:space="preserve">{l}</text>')
                else:
                    pop.append(tex(TX + 150, py + 48 + 44 * m, l, size=30, mode="text"))
            popups.append(f'<g id="sp-pop-{pid}" class="sp-pop">' + "".join(pop) + "</g>")
            css.append(f"svg:has(#sp-hit-{pid}:hover) #sp-pop-{pid} {{ opacity: 1; }}")

        popup(k, TX - 10, PX - TX - 30, [(l, "math") for key in pops.get(name, [name]) for l in st[key]])
        if name in examples:
            popup(f"x{k}", PX - 10, SX - PX - 60, examples[name])
        out += mark(PX + 20, y, now)
        if isinstance(note, tuple):  # a note with a link
            note, url = note
            out.append(f'<a href="{url}">' + text(PX + 56, y, escape(note), size=32, fill=INK, anchor="start",
                                                  extra=' text-decoration="underline"') + '</a>')
        elif note:
            out.append(text(PX + 56, y, escape(note), size=32, fill=INK, anchor="start"))
        if soon:
            out += mark(SX, y, soon)
        y += rh
    out.append("<style>.sp-pop { opacity: 0; pointer-events: none; transition: opacity 0.15s; } "
               + " ".join(css) + "</style>")
    out += hits  # on top of the table, so they receive the hover
    out += popups
    return svg(1600, y - rh + 46, "Standard path to consistency: weakening and substitution hold; transitivity "
               "of definitional equality and subject reduction fail but will hold after the kernel renovation; "
               "injectivity of ∀ is open; normalization and canonicity "
               "fail; consistency does not follow this way", out)


# ── A direct path: the interpretation, built up in reveal.js fragments ─────

def _frag(index, body, kind=""):
    # a reveal.js fragment; kind "fade-out" makes it disappear at that step
    return f'<g class="fragment {kind}" data-fragment-index="{index}">' + "".join(body) + "</g>"


def _hline(y):
    return f'<line x1="200" y1="{y}" x2="1400" y2="{y}" stroke="{CODE_LINE}" stroke-width="2"/>'


def interpretation():
    out = []
    # the signature
    out.append(tex(800, 50, r"\den{\cdot} : \lean{Expr} \to \mathbf{Set}, \qquad \text{for } \rho : \lean{Var} \to \mathbf{Set}",
                   "middle"))
    out.append(_hline(82))
    # simple cases, two columns
    out.append(tex(800, 110, r"\begin{aligned}"
                   r"\den{x} &= \rho(x) & \qquad \den{\Nat} &= \mathbb{N} & \qquad \den{\Empty} &= \emptyset \\[1.2ex]"
                   r"\den{\False} &= \emptyset & \den{\True} &= \{\pt\} & \den{\intro} &= \pt \\[1.2ex]"
                   r"\den{\Prop} &= \{\emptyset, \{\pt\}\} & \den{a = b} &= \pv(\den{a} = \den{b})"
                   r"\end{aligned}", "middle", valign="top"))
    out.append(tex(800, 375, r"\text{where}\quad \pv(\varphi) = \begin{cases} \{\pt\} & \text{if } \varphi \\ "
                   r"\emptyset & \text{otherwise} \end{cases}", "middle", size=28, fill=MUTED, valign="middle"))
    # the ∀ case, built up in steps
    EQ, FY = 470, 528
    out.append(tex(EQ, FY, r"\den{\fa{x}{A}{B}} = {}", "end", valign="middle"))
    # a question mark, gone at step 1
    out.append(_frag(1, [tex(EQ + 10, FY, "?", size=48, fill=RED, valign="middle")], "fade-out"))
    case2 = r"\prod_{v \in \den{A}} \den[\xv]{B} & \text{otherwise}"
    # step 1: the case split, with a syntactic guard
    syn = Tex(r"\begin{cases} \pv(\forall v \in \den{A},\ \den[\xv]{B} = \{\pt\}) & \text{if } B : \Prop \\[1.5ex] "
              + case2 + r"\end{cases}")
    # step 2: the semantic guard
    sem = Tex(r"\begin{cases} \pv(\forall v \in \den{A},\ \den[\xv]{B} = \{\pt\}) "
              r"& \text{if } \den[\xv]{B} \in \den{\Prop} \text{ for all } v \in \den{A} \\[1.5ex] " + case2 + r"\end{cases}")
    out.append(f'<g class="fragment" data-fragment-index="1"><g class="fragment fade-out" data-fragment-index="2">'
               + syn.at(EQ, FY, valign="middle")
               + text(EQ + syn.w + 50, FY - 34, "🤔", size=52, extra=f' font-family="{EMOJI}"') + "</g></g>")
    out.append(_frag(2, [sem.at(EQ, FY, valign="middle")]))
    # step 3: a consequence, set apart from the definition
    out.append(_frag(3, [_hline(FY + 125),
                         tex(800, FY + 200, r"\den{\Empty \to \True} = \{\pt\} = \den{\Empty \to \Nat}"
                             r" = \den{\Nat \to \Empty \to \Nat}", "middle")]))
    return svg(1600, FY + 240, "The interpretation: variables, sorts, Nat, True, False, equality and proofs, "
               "and a ∀ as a truth value or a dependent function space", out)


# ── The interpretation, continued: fun and application ──────────────────────

def interpretation2():
    out = [tex(800, 20, r"\begin{aligned}"
               r"\den{\fa{x}{A}{B}} &= \begin{cases} \pv(\forall v \in \den{A},\ \den[\xv]{B} = \{\pt\}) "
               r"& \text{if } \den[\xv]{B} \in \den{\Prop} \text{ for all } v \in \den{A} \\[1ex]"
               r"\prod_{v \in \den{A}} \den[\xv]{B} & \text{otherwise} \end{cases} \\[4ex]"
               r"\den{\lam{x}{A}{b}} &= \begin{cases} \pt & \text{if } \den[\xv]{b} = \pt \text{ for all } v \in \den{A} \\[1ex]"
               r"\{\, v \mapsto \den[\xv]{b} \mid v \in \den{A} \,\} & \text{otherwise} \end{cases} \\[4ex]"
               r"\den{f\;a} &= \den{f} \cdot \den{a} \qquad \text{where} \quad f \cdot v = \begin{cases}"
               r"\pt & \text{if } f = \pt \\ y & \text{if } (v \mapsto y) \in f \\ \emptyset & \text{otherwise}"
               r"\end{cases}"
               r"\end{aligned}", "middle", valign="top")]
    return svg(1600, 640, "The interpretation of ∀, fun and application; applying the point gives the point", out)


# ── Preservation, take 1 ─────────────────────────────────────────────────────

def _theorem_attempt(premise, counter):
    stmt = Tex(r"\textbf{Theorem (Preservation).} \textit{If $\vdash e \leadsto e'" + premise
               + r"$, then $\den{e} = \den{e'}$.}", mode="text")
    out = []
    # the statement, which gets struck through and marked at step 1
    out.append(_frag(1, [stmt.at(60, 70)], "fade-out"))
    out.append(_frag(1, [stmt.at(60, 70, fill=MUTED),
                         f'<line x1="56" y1="61" x2="{64 + stmt.w:.0f}" y2="61" stroke="{MUTED}" stroke-width="2.5"/>',
                         f'<circle cx="1540" cy="58" r="20" fill="{RED}"/>'
                         '<path d="M1532 50 L1548 66 M1548 50 L1532 66" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>']))
    out.append(_frag(1, [tex(60, 160, r"\textit{Counterexample.}", mode="text"),
                         *[tex(110, 230 + 70 * i, l, size=32) for i, l in enumerate(counter)]]))
    return out


def preservation_take1():
    redex = r"(\lam{x}{\Nat}{x})\;\intro"
    counter = [redex + r" \leadsto \intro, \quad \text{but}",
               r"\den{" + redex + r"} = \{\, v \mapsto v \mid v \in \mathbb{N} \,\} \cdot \pt = \emptyset \neq \pt = \den{\intro}"]
    out = _theorem_attempt("", counter)
    return svg(1600, 390, "Preservation, first attempt: reduction does not preserve the interpretation of ill-formed terms", out)


# ── Well-denoted terms ──────────────────────────────────────────────────────

def well_denoted():
    V = r"\forall v \in \den{A}:\ "
    z = 30
    out = []
    # application of a graph: the argument lies in its domain, a type
    out += _rule(800, 30, [r"\ok{f}", r"\ok{a}", r"\den{f} = \{\, v \mapsto F(v) \mid v \in A' \,\}",
                            r"A' \text{ a type}", r"\den{a} \in A'"], r"\ok{f\;a}", "app-graph", size=z)
    # application of a proof: anything goes
    out += _rule(800, 220, [r"\ok{f}", r"\ok{a}", r"\den{f} = \pt"], r"\ok{f\;a}", "app-pt", size=z)
    out += _rule(800, 410, [r"\ok{A}", r"\den{A} \text{ a type}", V + r"\ok[\xv]{b}"],
                 r"\ok{\lam{x}{A}{b}}", "fun", size=z)
    out += _rule(800, 600, [r"\ok{A}", r"\den{A} \text{ a type}", V + r"\ok[\xv]{B},\ \den[\xv]{B} \text{ a type}"],
                 r"\ok{\fa{x}{A}{B}}", r"$\forall$", size=z)
    out.append(tex(800, 810, r"\textit{a type}: $\emptyset$, $\{\pt\}$, or a set $X \neq \pt$ with $\pt \notin X$",
                   "middle", size=28, fill=MUTED, mode="text"))
    return svg(1600, 840, "Rules for well-denoted terms: the point may be applied to anything, a graph "
               "to a member of its domain, which is a type; a binder's domain is a type, and a ∀'s fibres are types", out)


# ── Preservation, take 2 ─────────────────────────────────────────────────────

def preservation_take2():
    redex = r"(\lam{h}{\False}{h})\;\lean{0}"
    counter = [r"\ok{" + redex + r"} \quad \text{and} \quad " + redex + r" \leadsto \lean{0}, \quad \text{but}",
               r"\den{" + redex + r"} = \pt \cdot 0 = \pt \neq 0 = \den{\lean{0}}"]
    out = _theorem_attempt(r",\ \ok{e}", counter)
    return svg(1600, 390, "Preservation, second attempt: a well-denoted redex that denotes the point reduces to "
               "something else", out)


# ── Preservation up to a point ───────────────────────────────────────────────

def preservation_point():
    out = []
    out.append(tex(60, 70, r"\textbf{Theorem (Preservation).} \textit{If $\vdash e \leadsto e'$, $\ok{e}$ and "
                   r"$\den{e} \neq \pt$, then $\ok{e'}$ and $\den{e} = \den{e'}$.}", mode="text"))
    lam = r"\lam{x}{A}{b}"
    redex = "(" + lam + r")\;a"
    out.append(_frag(1, [tex(60, 170, r"\text{\textit{Proof} (case $\beta$).} \qquad \begin{aligned}[t]"
                             r"\den{" + redex + r"} \neq \pt &\implies \den{" + lam + r"} \neq \pt \\[1ex]"
                             r"&\implies \den{" + lam + r"} \text{ is a function graph on } \den{A} \\[1ex]"
                             r"&\implies \den{a} \in \den{A} \qquad (\text{by } \ok{" + redex + r"}) \\[1ex]"
                             r"&\implies \den{" + redex + r"} = \den[\rho,\, x \mapsto \den{a}]{b}"
                             r" = \den{b[x \coloneqq a]} \quad \checkmark"
                             r"\end{aligned}", size=32)]))
    out.append(_frag(2, [_hline(440),
                         tex(800, 510, r"\textit{Intuition:} the assumption $\den{e} \neq \pt$ ripples through the proof,",
                             "middle", size=32, mode="text"),
                         tex(800, 565, "and disappears where we can use proof irrelevance.", "middle", size=32,
                             mode="text")]))
    return svg(1600, 600, "Preservation up to a point: reduction preserves the interpretation of well-denoted terms "
               "that do not denote the point, with the proof for β", out)


# ── The certification tax: lambda congruence with extra premises ──────────────

def certification_tax():
    G = r"\Gamma \vdash "
    Gx = r"\Gamma,\, x : A_2 \vdash "
    concl = G + r"\lam{x}{A_1}{b_1} \equiv \lam{x}{A_2}{b_2}"
    lean = [G + r"A_1 \equiv A_2", Gx + r"b_1 \equiv b_2"]
    extra = [Gx + r"b_1 \Rightarrow t_1", Gx + r"b_2 \Rightarrow t_2", Gx + r"t_1 \equiv t_2"]
    out = []
    out.append(tex(60, 50, "Lean's kernel", size=30, fill=MUTED, mode="text"))
    out += _rule(800, 90, lean, concl, "lam", size=34)
    out.append(tex(60, 300, "con-leche", size=30, fill=MUTED, mode="text"))
    # the premises on two lines: Lean's two, then the three extra ones just above the bar
    # the premises are set beforehand, as mathpartir does not take an \halign as a premise
    out.append(tex(800, 340, r"\sbox\pb{$\twolines{" + r" \qquad ".join(lean) + r"}{\color{amber} "
                   + r" \qquad ".join(extra) + r"}$}$\inferrule*[right=\rn{lam}]{\usebox\pb}{" + concl + "}$",
                   "middle", size=34, mode="text", valign="top"))
    return svg(1600, 560, "Lambda congruence in Lean's kernel, and in con-leche with three extra premises that infer "
               "and compare the types of the two bodies", out)


# ── Sorts and universes ─────────────────────────────────────────────────────

def sorts_universes():
    out = []
    out.append(tex(800, 60, r"\Prop = \srt{\lean{0}} \;:\; \srt{\lean{1}} \;:\; \srt{\lean{2}} \;:\; \srt{\lean{3}}"
                   r" \;:\; \cdots", "middle", size=36))
    out.append(_hline(110))
    out.append(tex(800, 150, r"\begin{aligned}"
                   r"\den{\srt{\lean{0}}} &= \den{\Prop} = \{\emptyset, \{\pt\}\} \\[2ex]"
                   r"\den{\srt{n}} &= \{\, X \in U_n \mid X \text{ is a type} \,\} \mathrlap{\qquad \muted{\text{for } n \geq 1}}"
                   r"\end{aligned}", "middle", valign="top"))
    out.append(tex(800, 400, r"\text{where} \quad U_1 \in U_2 \in U_3 \in \cdots \quad \text{are Grothendieck universes}",
                   "middle"))
    out.append(tex(800, 450, "(transitive, closed under pairing, union, power set and replacement)", "middle", size=28,
                   fill=MUTED, mode="text"))
    out.append(_hline(510))
    out.append(tex(800, 590, "Assuming this chain saves us from Gödel.", "middle", size=36, mode="text"))
    return svg(1600, 630, "Sorts and universes: Prop is Sort 0, a sort denotes the types of a Grothendieck universe; "
               "assuming a chain of them saves us from Gödel", out)


# ── Inductive types: least fixed points, and accessibility ────────────────

def inductive_types():
    kw = lambda s: (s, KW, 700)
    pl = lambda s: (s, INK, 400)
    cn = lambda s: (s, CONST, 400)
    out = []
    # List
    c, h = code(40, 30, [[kw("inductive"), pl(" "), cn("List"), pl(" (α : Type u) "), kw("where")],
                         [pl("  | nil  : "), cn("List"), pl(" α")],
                         [pl("  | cons : α → "), cn("List"), pl(" α → "), cn("List"), pl(" α")]], size=26, w=640)
    out += c
    out.append(tex(740, 30 + h / 2, r"\den{\List\;\alpha} = \mu X.\ 1 + \den{\alpha} \times X", valign="middle"))
    # Tree, nested through List
    c, h2 = code(40, 200, [[kw("inductive"), pl(" "), cn("Tree"), pl(" "), kw("where")],
                           [pl("  | node : "), cn("List"), pl(" "), cn("Tree"), pl(" → "), cn("Tree")]], size=26, w=640)
    out += c
    out.append(tex(740, 200 + h2 / 2, r"\den{\Tree} = \mu X.\ \den{\List}(X)", valign="middle"))
    out.append(tex(1500, 200 + h2 / 2, r"($\mu$: least fixed point)", "end", size=26, fill=MUTED, mode="text",
                   valign="middle"))
    # the second half appears on the next step
    k = len(out)
    out.append(_hline(355))
    out.append(tex(60, 420, r"The checker checks: $X$ occurs only \textbf{strictly positively} (syntactic positivity)",
                   mode="text"))
    out.append(tex(60, 490, r"$\Longrightarrow$\ the operator $\Phi$ (e.g.\ $X \mapsto 1 + \den{\alpha} \times X$) "
                   r"is \textbf{accessible} with a bound $A \in U_n$:", mode="text"))
    out.append(tex(800, 580, r"x \in \Phi(W) \implies \exists W_0 \subseteq W,\ |W_0| \leq |A|,\ "
                   r"\forall W' \supseteq W_0.\ x \in \Phi(W')", "middle"))
    out.append(tex(800, 650, r"every element depends on at most $|A|$-many elements of the input", "middle", size=28,
                   fill=MUTED, mode="text"))
    out.append(tex(60, 735, r"$\Longrightarrow$\ $\Phi$ is monotone, so the least fixed point exists, and it lies in "
                   r"$U_n$ (the right universe)", mode="text"))
    out[k:] = [_frag(1, out[k:])]
    return svg(1600, 780, "Inductive types as least fixed points: List and Tree nested through List; the checker must "
               "ensure the operator is accessible, which puts the fixed point in the right universe and makes it "
               "monotone", out)


# ── The con-leche family: layers, proofs, and what runs ─────────────────
# Sources: the READMEs and OVERVIEW.md of leanprover/con-leche, con-ron, con-agua (Nov 2026).

def checker_family():
    import math
    AMB, AMB_BG = "#b45309", "#fffbeb"
    W, CW, BH, RH, TOP = 1600, 380, 76, 140, 110
    COLS = [40, 610, 1180]

    def top(k):  # levels counted from the bottom; extra room above the row that runs
        return TOP + (4 - k) * RH + (36 if k <= 1 else 0)

    out = []
    for x, name, lang in zip(COLS, ["con-leche", "con-ron", "con-agua"], ["in Lean", "in Rust", "in x86 assembly"]):
        out.append(text(x + CW / 2, 44, name, size=32, weight=700, fill=INK))
        out.append(text(x + CW / 2, 74, lang, size=21, fill=MUTED))
    # what runs: the bottom two rows, thanks to bottom alignment
    out.append(rect(COLS[0] - 18, top(1) - 12, COLS[2] + CW - COLS[0] + 36, top(0) - top(1) + BH + 24, rx=14, fill="none",
                    stroke=INK, sw=4))
    out.append(rect(COLS[0] - 2, top(1) - 26, 132, 28, rx=4, fill="#ffffff"))
    out.append(text(COLS[0] + 8, top(1) - 4, "WHAT RUNS", size=19, weight=700, fill=INK, anchor="start",
                    extra=' letter-spacing="2"'))

    def box(col, k, title, sub, trusted=False):
        x, y = COLS[col], top(k)
        out.append(rect(x, y, CW, BH, rx=12, fill=AMB_BG if trusted else GREEN_BG,
                        stroke=AMB if trusted else GREEN, sw=2))
        out.append(text(x + CW / 2, y + (32 if sub else 47), title, size=27, weight=600, fill=INK))
        if sub:
            out.append(text(x + CW / 2, y + 61, sub, size=19, fill=MUTED))

    def up(col, k, labels, trusted=False):  # from level k up to level k+1
        cx = COLS[col] + CW / 2
        color = AMB if trusted else GREEN
        out.append(arrow(cx, top(k), cx, top(k + 1) + BH, color=color, sw=3, head=14, dash=trusted))
        mid = (top(k + 1) + BH + top(k) - (12 if k == 1 else 0)) / 2 + 7
        for i, (lab, c) in enumerate(labels):
            out.append(text(cx + 16, mid + (i - (len(labels) - 1) / 2) * 23, lab, size=20, weight=600,
                            fill=c or color, anchor="start"))

    def across(c1, k1, c2, k2, label):  # from a box's side to a box in the neighbouring column
        x1 = COLS[c1] if c2 < c1 else COLS[c1] + CW
        x2 = COLS[c2] + CW if c2 < c1 else COLS[c2]
        y1, y2 = top(k1) + BH / 2, top(k2) + BH / 2
        out.append(arrow(x1, y1, x2, y2, color=GREEN, sw=3, head=14))
        (lx, ly), (rx_, ry) = sorted([(x1, y1), (x2, y2)])
        a = math.atan2(ry - ly, rx_ - lx)
        mx, my = (lx + rx_) / 2 + 12 * math.sin(a), (ly + ry) / 2 - 12 * math.cos(a)
        out.append(text(mx, my, label, size=20, weight=600, fill=GREEN,
                        extra=f' transform="rotate({math.degrees(a):.1f} {mx:.1f} {my:.1f})"'))

    # con-leche
    box(0, 4, "Set-theoretic model", "assumed: ZF + ω universes", trusted=True)
    box(0, 3, "Relational view", "inductive rules")
    box(0, 2, "Pure checker", "fueled")
    box(0, 1, "Cached checker", "memo tables")
    box(0, 0, "Lean compiler & runtime", "incl. bignums", trusted=True)
    up(0, 3, [("soundness", None)])
    up(0, 2, [("bridge", None)])
    up(0, 1, [("refinement", None)])
    # con-ron
    box(1, 3, "Lean twin", "Rust’s data structures")
    box(1, 2, "Lean model of the Rust", "generated by Aeneas")
    box(1, 1, "Rust code", None)
    box(1, 0, "Rust compiler & runtime", None, trusted=True)
    up(1, 2, [("refinement", None)])
    up(1, 1, [("Aeneas translation", None)], trusted=True)
    across(1, 3, 0, 2, "refinement")
    # con-agua
    box(2, 2, "L code", "small low-level language")
    box(2, 1, "x86 assembly", None)
    box(2, 0, "Assembler", "+ linker, C harness", trusted=True)
    up(2, 1, [("verified compiler", None), ("Kraken x86 semantics", AMB)])
    across(2, 2, 1, 3, "refinement")

    # legend
    ly = top(0) + BH + 72
    out.append(rect(COLS[0], ly - 22, 30, 30, rx=6, fill=GREEN_BG, stroke=GREEN, sw=2))
    out.append(text(COLS[0] + 44, ly, "proved in Lean", size=22, fill=MUTED, anchor="start"))
    out.append(rect(COLS[0] + 260, ly - 22, 30, 30, rx=6, fill=AMB_BG, stroke=AMB, sw=2))
    out.append(text(COLS[0] + 304, ly, "trusted", size=22, fill=MUTED, anchor="start"))
    return svg(W, ly + 20, "The con-leche family of checkers. con-leche: a cached checker refines a fueled pure "
               "checker, which bridges to relational rules, sound for a set-theoretic model; it runs on Lean's "
               "compiler and runtime. con-ron: Rust code, via an Aeneas translation, refines a Lean twin that "
               "refines con-leche's pure checker. con-agua: x86 assembly from a verified compiler, against "
               "Kraken's x86 semantics, refines L code that refines con-ron's twin.", out)


# ── Backup: why the point is not ∅ ─────────────────────────────────────
# con-leche: pt = {ptTag}, ptTag = {∅, {{∅}}}, chosen so that no value of a data type is pt
# (ConLeche/SetTheory/Derive/Pt.lean).

def point_not_empty():
    out = [tex(800, 40, r"\text{Suppose } \pt = \emptyset", "middle", size=40, valign="top")]
    # the gain
    out.append(tex(160, 190, r"f \cdot v = \begin{cases} y & \text{if } (v \mapsto y) \in f \\ "
                   r"\emptyset & \text{otherwise} \end{cases}", valign="middle"))
    out.append(tex(1000, 190, "one case fewer", size=30, fill=GREEN, mode="text", valign="middle"))
    out.append(_hline(290))
    # the problems
    out.append(tex(160, 360, r"\den{\False} = \den{\Empty} = \emptyset = \pt", valign="middle"))
    out.append(tex(1000, 360, "a type is the point", size=30, fill=RED, mode="text", valign="middle"))
    out.append(tex(160, 440, r"\den{\Prop} = \{\emptyset, \{\pt\}\} = \{\pt, \{\pt\}\}", valign="middle"))
    out.append(tex(1000, 440, "a type holds the point and more", size=30, fill=RED, mode="text", valign="middle"))
    out.append(_hline(520))
    # what is lost
    lost = [
        r"a type is $\emptyset$, $\{\pt\}$, or a set $X \neq \pt$ with $\pt \notin X$",
        r"two members of one type: both $\pt$ or neither \muted{(the defeq shortcut for proofs)}",
        r"preservation for terms that do not denote $\pt$ \muted{(would exclude $\False$, $\Empty$)}",
    ]
    for i, line in enumerate(lost):
        y = 590 + i * 70
        out.append(tex(160, y, r"\color[HTML]{dc2626}\times", size=34, valign="middle"))
        out.append(tex(210, y, line, size=30, mode="text", valign="middle"))
    return svg(1600, 770, "If the point were the empty set, application would have one case fewer, but False and "
               "Empty would denote the point and Prop would contain it, so types would no longer be either the point's "
               "truth values or sets without the point, the proof shortcut for definitional equality would go, and "
               "preservation for terms that do not denote the point would exclude False and Empty", out)


FIGURES = {
    "point-not-empty.svg": point_not_empty,
    "checker-family.svg": checker_family,
    "inductive-types.svg": inductive_types,
    "sorts-universes.svg": sorts_universes,
    "certification-tax.svg": certification_tax,
    "interpretation2.svg": interpretation2,
    "preservation-take1.svg": preservation_take1,
    "well-denoted.svg": well_denoted,
    "preservation-take2.svg": preservation_take2,
    "preservation-point.svg": preservation_point,
    "interpretation.svg": interpretation,
    "standard-path.svg": standard_path,
    "typing-rules.svg": typing_rules,
    "judgments.svg": judgments,
    "checker.svg": checker,
    "comparator.svg": comparator,
    "attacks.svg": attacks,
    "threat-models.svg": threat_models,
    "architecture.svg": architecture,
    "history.svg": history,
    "why-lean.svg": why_lean,
    "type-theory-sugar.svg": sugar,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    contents = {name: fn() for name, fn in FIGURES.items()}
    if _tex_missing:
        _tex_render()
        contents = {name: fn() for name, fn in FIGURES.items()}
    for name, content in contents.items():
        path = os.path.join(OUT, name)
        # Only touch changed files, so the live preview does not rebuild in a loop.
        try:
            with open(path, encoding="utf-8") as f:
                if f.read() == content:
                    continue
        except FileNotFoundError:
            pass
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote", os.path.join("static", "images", name))
