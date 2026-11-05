import argparse, base64, io, os
from fontTools.ttLib import TTFont
from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
THEMES = {
    "dark": dict(SUFFIX="", GREEN="#4ef185", BONE="#e9e7e2", ASH="#c3c1bc", DIM="#5d5c58", FAINT="#232322", NIGHT="#050505",
                 MID="#8d8b86", ZERO="#3a3a38", EDGE="#2a2a29", WATER="#2c2c2b", MUTE_EDGE="#4a4a48", MUTE="#93918b"),
    "light": dict(SUFFIX="-light", GREEN="#11843f", BONE="#121212", ASH="#3d3d3b", DIM="#8a8984", FAINT="#dcdbd5", NIGHT="#f4f3ef",
                  MID="#6b6a66", ZERO="#c9c8c2", EDGE="#d6d5cf", WATER="#e2e1db", MUTE_EDGE="#b5b4ae", MUTE="#6b6a66"),
}


def use(theme):
    globals().update(THEMES[theme])


use("dark")
FILES = {"mono": "IBMPlexMono-Regular.ttf", "sans": "IBMPlexSans-Regular.ttf", "mincho": "ShipporiMincho-Medium.ttf"}
FAMILY = {"mono": "M", "sans": "S", "mincho": "K"}
_fonts = {}


def font(key):
    if key not in _fonts:
        _fonts[key] = TTFont(os.path.join(FONT_DIR, FILES[key]))
    return _fonts[key]


def width(key, text, size):
    f = font(key)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), cmap[32])][0] for c in text) * size / upm


def wrap(key, text, size, max_width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and width(key, trial, size) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def woff2(key, text):
    buf = io.BytesIO()
    font(key).save(buf)
    buf.seek(0)
    sub = TTFont(buf)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.name_IDs = []
    opts.layout_features = ["kern", "liga"]
    opts.notdef_outline = True
    subsetter = subset.Subsetter(opts)
    subsetter.populate(text=text + " ")
    subsetter.subset(sub)
    out = io.BytesIO()
    sub.flavor = "woff2"
    sub.save(out)
    return out.getvalue()


def faces(texts):
    css = ""
    for key, text in texts.items():
        data = base64.b64encode(woff2(key, text)).decode()
        css += '@font-face{font-family:"%s";src:url(data:font/woff2;base64,%s) format("woff2")}' % (FAMILY[key], data)
    return css + ".m{font-family:M}.s{font-family:S}.k{font-family:K}"


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write(name, parts):
    with open(os.path.join(ASSETS, name.replace(".svg", SUFFIX + ".svg")), "w") as fh:
        fh.write("".join(parts))


def header():
    W, H = 1280, 330
    payload = ("Raian Suzuki\0games\0procedural tools\0AI systems\0reverse engineering\0"
               "Everlasting Odyssey\0Skyrim\0Polyspoon\0StillWrong\0neuron-soul\0LIA\0").encode()
    payload = (payload * 2)[:16 * 11]
    rows = [payload[i:i + 16] for i in range(0, len(payload), 16)]
    code = [
        [("k", "void "), ("f", "raian_suzuki"), ("p", "(void) {")],
        [("i", "  build"), ("p", "(games);")],
        [("i", "  build"), ("p", "(procedural_tools);")],
        [("i", "  build"), ("p", "(ai_systems);")],
        [("i", "  reverse"), ("p", "(software_i_want_to_change);")],
        [("i", "  while "), ("p", "(model.flawed) harness++;")],
        [("p", "}")],
    ]
    xref = "; xref  doyoutrustlia.com/raian"
    title_l, title_r = "raian.exe · FUN_00401000", "decompile: raian_suzuki"
    ascii_rows = ["".join(chr(b) if 32 <= b < 127 else "." for b in r) for r in rows]
    mono_text = "0123456789ABCDEF" + "".join(ascii_rows) + "".join(s for l in code for _, s in l) + xref + title_l + title_r
    step = 22
    css = faces({"mono": mono_text, "mincho": "悔"}) + (
        "@keyframes scan{0%%{transform:translateY(0)}100%%{transform:translateY(%dpx)}}" % (len(rows) * step) +
        ".bar{animation:scan 9s steps(%d) infinite}" % len(rows) +
        "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1.1s steps(1) infinite}")
    t = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
         'aria-label="Raian Suzuki builds games, procedural tools and AI systems, and reverse engineers the software he wants to change.">' % (W, H, W, H),
         "<style>" + css + "</style>", '<rect width="100%%" height="100%%" fill="%s"/>' % NIGHT]
    t.append('<text class="m" x="40" y="40" font-size="12" fill="%s">%s</text>' % (DIM, esc(title_l)))
    t.append('<text class="m" x="720" y="40" font-size="12" fill="%s">%s</text>' % (DIM, esc(title_r)))
    t.append('<path d="M40 54H640M720 54H1240M680 54V306" stroke="%s"/>' % FAINT)
    t.append('<rect class="bar" x="36" y="64" width="608" height="%d" fill="%s" fill-opacity=".09"/>' % (step, GREEN))
    name_len = len("Raian Suzuki")
    for r, row in enumerate(rows):
        y = 80 + r * step
        t.append('<text class="m" x="44" y="%d" font-size="13" fill="%s">%08X</text>' % (y, DIM, 0x401000 + r * 16))
        for c, b in enumerate(row):
            i = r * 16 + c
            col = GREEN if i < name_len else (MID if b else ZERO)
            t.append('<text class="m" x="%d" y="%d" font-size="13" fill="%s">%02X</text>' % (130 + c * 23, y, col, b))
        t.append('<text class="m" x="508" y="%d" font-size="13" fill="%s" xml:space="preserve">%s</text>' % (y, BONE if r == 0 else ASH, esc(ascii_rows[r])))
    t.append('<rect x="125" y="66" width="%d" height="20" fill="none" stroke="%s"/>' % (name_len * 23 + 2, GREEN))
    colors = {"k": MID, "f": BONE, "i": GREEN, "p": ASH}
    for li, line in enumerate(code):
        y = 94 + li * 30
        spans = "".join('<tspan fill="%s">%s</tspan>' % (colors[k], esc(s)) for k, s in line)
        t.append('<text class="m" x="724" y="%d" font-size="17" xml:space="preserve">%s</text>' % (y, spans))
    last_y = 94 + (len(code) - 1) * 30
    t.append('<rect class="cur" x="%.0f" y="%d" width="9" height="18" fill="%s"/>' % (724 + width("mono", "} ", 17), last_y - 14, GREEN))
    t.append('<text class="m" x="724" y="%d" font-size="12" fill="%s">%s</text>' % (last_y + 34, DIM, esc(xref)))
    t.append('<text class="k" x="1240" y="306" font-size="22" text-anchor="end" fill="%s">悔</text>' % DIM)
    t.append("</svg>")
    write("header.svg", t)


def about():
    W = 1280
    intro = ("I develop through AI, and I build the engineering that makes that fast and reliable: bounded tasks, durable state, "
             "independent checks and recovery. Game development at TapOrbit Studios (Everlasting Odyssey, Zombie Citizen), "
             "Skyrim's combat AI rebuilt from the shipped binary, generators for trees, villages, textures, effects and audio.")
    title = ".text:00401800  ; about"
    cta = "click here for my portfolio"
    target = "jmp doyoutrustlia.com/raian"
    lines = wrap("sans", intro, 19, 1150)
    top = 96
    box_y = top + len(lines) * 32 + 18
    H = box_y + 76
    mono_text = title + cta + target + "→0123456789ABCDEF:"
    css = faces({"mono": mono_text, "sans": intro}) + (
        "@keyframes pulse{0%%,100%%{stroke-opacity:1}50%%{stroke-opacity:.35}}.btn{animation:pulse 2.4s ease-in-out infinite}"
        "@keyframes nudge{0%%,100%%{transform:translateX(0)}50%%{transform:translateX(6px)}}.arr{animation:nudge 1.6s ease-in-out infinite}")
    t = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s Click here for my portfolio at doyoutrustlia.com/raian.">' % (W, H, W, H, esc(intro)),
         "<style>" + css + "</style>", '<rect width="100%%" height="100%%" fill="%s"/>' % NIGHT]
    t.append('<text class="m" x="40" y="40" font-size="12" xml:space="preserve"><tspan fill="%s">.text:00401800</tspan><tspan fill="%s">  ; about</tspan></text>' % (DIM, BONE))
    t.append('<path d="M40 54H1240" stroke="%s"/>' % FAINT)
    for i, l in enumerate(lines):
        y = top + i * 32
        t.append('<text class="m" x="40" y="%d" font-size="12" fill="%s">%06X</text>' % (y - 2, DIM, 0x401800 + i * 0x20))
        t.append('<text class="s" x="112" y="%d" font-size="19" fill="%s">%s</text>' % (y, ASH, esc(l)))
    bw = width("mono", cta, 15) + 70
    t.append('<rect class="btn" x="112" y="%d" width="%.0f" height="44" fill="%s" fill-opacity=".07" stroke="%s"/>' % (box_y, bw, GREEN, GREEN))
    t.append('<text class="m" x="132" y="%d" font-size="15" fill="%s">%s</text>' % (box_y + 28, GREEN, esc(cta)))
    t.append('<text class="m arr" x="%.0f" y="%d" font-size="15" fill="%s">→</text>' % (112 + bw - 34, box_y + 28, GREEN))
    t.append('<text class="m" x="%.0f" y="%d" font-size="13" fill="%s">; %s</text>' % (112 + bw + 24, box_y + 27, DIM, esc(target)))
    t.append("</svg>")
    write("about.svg", t)


CARDS = [
    ("polyspoon", "Polyspoon", "An open-source 3D asset community. Small TypeScript recipes become editable low-poly models for Unity and Godot, every model reviewed by a person.", "Public", "JavaScript"),
    ("stillwrong", "StillWrong", "Unity Editor package. See a bug while you play, click it and say what is wrong. An agent fixes a copy of the scene on its own git branch.", "Public", "C# · Meta hackathon"),
    ("neuron-soul", "neuron-soul", "Contrastive neuron extraction and steering. Which MLP neurons hold one character archetype inside Qwen models, and what pushing them does.", "Public", "Python · 4B and 27B"),
    ("elai", "ELAI", "Local-first, model-agnostic agent-harness research and its Zenodo preprint. Restart planned; old claims await revalidation.", "Archive", "Rust"),
    ("lia-trust", "LIA trust kernel", "Fail-closed gates and Ed25519-signed receipts for coding-agent actions. Anyone can verify the journal offline.", "v0.3.0", "Rust · Python"),
    ("understudy", "Understudy", "Show a support procedure once in the page, and the page registers it as a callable WebMCP tool.", "Public", "TypeScript"),
]


def card(index, slug, title, lede, status, meta):
    W, H = 640, 236
    addr = 0x401A40 + index * 0x2C0
    head = "sub_%06X · .text" % addr
    symbol = slug.replace("-", "_")
    raw = (slug + "\0" + meta + "\0").encode()
    hexrows = [" ".join("%02X" % b for b in (raw * 4)[i * 6:(i + 1) * 6]) for i in range(6)]
    lines = wrap("sans", lede, 15.5, 400)
    green = status == "Public" or status.startswith("v")
    mono_text = head + symbol + "():" + status + meta + "".join(hexrows) + "0123456789ABCDEF;"
    t = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s. %s">' % (W, H, W, H, esc(title), esc(lede)),
         "<style>" + faces({"mono": mono_text, "sans": lede, "mincho": title}) + "</style>"]
    t.append('<rect x=".5" y=".5" width="%d" height="%d" fill="%s" stroke="%s"/>' % (W - 1, H - 1, NIGHT, EDGE))
    t.append('<text class="m" x="28" y="36" font-size="11.5" fill="%s">%s</text>' % (DIM, esc(head)))
    t.append('<text class="m" x="612" y="36" font-size="11.5" text-anchor="end" fill="%s">%s():</text>' % (ZERO, esc(symbol)))
    t.append('<text class="k" x="27" y="80" font-size="30" fill="%s">%s</text>' % (BONE, esc(title)))
    t.append('<path d="M28 96h48" stroke="%s"/>' % GREEN)
    for i, l in enumerate(lines):
        t.append('<text class="s" x="28" y="%d" font-size="15.5" fill="%s">%s</text>' % (126 + i * 23, ASH, esc(l)))
    for i, row in enumerate(hexrows):
        t.append('<text class="m" x="612" y="%d" font-size="11" text-anchor="end" fill="%s">%s</text>' % (78 + i * 19, WATER, row))
    sw = width("mono", status, 11) + 18
    t.append('<rect x="28" y="196" width="%.1f" height="20" fill="none" stroke="%s"/>' % (sw, GREEN if green else MUTE_EDGE))
    t.append('<text class="m" x="37" y="210" font-size="11" fill="%s">%s</text>' % (GREEN if green else MUTE, esc(status)))
    t.append('<text class="m" x="%.1f" y="210" font-size="11" fill="%s">; %s</text>' % (28 + sw + 14, DIM, esc(meta)))
    t.append("</svg>")
    write("card-%s.svg" % slug, t)


def divider(name, addr, label):
    W, H = 1280, 56
    text = addr + "; " + label
    t = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, H, W, H, esc(label)),
         "<style>" + faces({"mono": text}) + "</style>",
         '<rect width="100%%" height="100%%" fill="%s"/>' % NIGHT,
         '<text class="m" x="40" y="34" font-size="13" xml:space="preserve"><tspan fill="%s">%s</tspan><tspan fill="%s">  ; %s</tspan></text>' % (DIM, esc(addr), BONE, esc(label))]
    end = 40 + width("mono", addr + "  ; " + label, 13) + 24
    t.append('<path d="M%.0f 30H1240" stroke="%s"/><rect x="%.0f" y="27" width="6" height="6" fill="%s"/>' % (end, FAINT, end - 10, GREEN))
    t.append("</svg>")
    write("divider-%s.svg" % name, t)


def action_font():
    chars = "".join(chr(c) for c in range(32, 127)) + "·"
    with open(os.path.join(ASSETS, "fonts", "mono.woff2"), "wb") as fh:
        fh.write(woff2("mono", chars))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonts", required=True)
    FONT_DIR = parser.parse_args().fonts
    for theme in THEMES:
        use(theme)
        header()
        about()
        for i, c in enumerate(CARDS):
            card(i, *c)
        divider("work", ".text:00401A00", "selected work")
    action_font()
