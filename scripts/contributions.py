import base64, datetime, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUERY = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
         "totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
THEMES = {
    "contributions.svg": {
        "bg": "#050505", "text": "#e9e7e2", "dim": "#5d5c58", "rule": "#232322", "green": "#4ef185", "hot": "#d6ffe2",
        "levels": {"NONE": "#141414", "FIRST_QUARTILE": "#3a3a38", "SECOND_QUARTILE": "#6e6d69",
                   "THIRD_QUARTILE": "#b4b2ad", "FOURTH_QUARTILE": "#4ef185"}},
    "contributions-light.svg": {
        "bg": "#f4f3ef", "text": "#121212", "dim": "#8a8984", "rule": "#dcdbd5", "green": "#11843f", "hot": "#2fc56a",
        "levels": {"NONE": "#e4e3dd", "FIRST_QUARTILE": "#c9c8c2", "SECOND_QUARTILE": "#9d9c97",
                   "THIRD_QUARTILE": "#5f5e5a", "FOURTH_QUARTILE": "#11843f"}},
}


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": "bearer " + token, "Content-Type": "application/json", "User-Agent": "profile-contributions"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    user = (data.get("data") or {}).get("user")
    if data.get("errors") or not user:
        raise SystemExit("GitHub API error: %s" % data.get("errors"))
    return user["contributionsCollection"]["contributionCalendar"]


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if counts[i] == 0:
        i -= 1
    current = 0
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    return current, longest


def render(cal, p, font):
    weeks = cal["weeks"][-53:]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = cal["totalContributions"]
    busiest = max(d["contributionCount"] for d in days)
    current, longest = streaks(days)
    W, H, x0, y0, cell, step = 1280, 300, 40, 92, 18, 22.3
    left = "%s CONTRIBUTIONS · LAST 12 MONTHS" % format(total, ",")
    right = "BUSIEST DAY %d · CURRENT STREAK %d · LONGEST %d" % (busiest, current, longest)
    t = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s, %s">' % (W, H, W, H, left.lower(), right.lower()),
         '<style>@font-face{font-family:"M";src:url(data:font/woff2;base64,%s) format("woff2")}.m{font-family:M}'
         '@keyframes scan{0%%{transform:translateX(0)}100%%{transform:translateX(%.1fpx)}}.bar{animation:scan 14s steps(%d) infinite}'
         '@keyframes hot{0%%,100%%{fill:%s}50%%{fill:%s}}.h{animation:hot 3s ease-in-out infinite}</style>' % (font, len(weeks) * step, len(weeks), p["green"], p["hot"]),
         '<rect width="100%%" height="100%%" fill="%s"/>' % p["bg"],
         '<text class="m" x="40" y="40" font-size="12" fill="%s" xml:space="preserve">.data:00402000  <tspan fill="%s">; contributions</tspan></text>' % (p["dim"], p["text"]),
         '<text class="m" x="1240" y="40" font-size="12" text-anchor="end" fill="%s">through %s</text>' % (p["dim"], days[-1]["date"]),
         '<path d="M40 54H1240" stroke="%s"/>' % p["rule"]]
    prev = None
    for wi, w in enumerate(weeks):
        month = int(w["contributionDays"][0]["date"][5:7])
        if month != prev and wi < len(weeks) - 2:
            t.append('<text class="m" x="%.1f" y="80" font-size="11" fill="%s">%s</text>' % (x0 + wi * step, p["dim"], MONTHS[month - 1]))
        prev = month
    t.append('<rect class="bar" x="%.1f" y="%d" width="%.1f" height="%.1f" fill="%s" fill-opacity=".1"/>' % (x0 - 2.1, y0 - 2, step, 7 * step, p["green"]))
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            row = datetime.date.fromisoformat(d["date"]).isoweekday() % 7
            level = d["contributionLevel"]
            cls = ' class="h"' if level == "FOURTH_QUARTILE" else ""
            t.append('<rect%s x="%.1f" y="%.1f" width="%d" height="%d" rx="2" fill="%s"><title>%s: %d</title></rect>' % (
                cls, x0 + wi * step, y0 + row * step, cell, cell, p["levels"][level], d["date"], d["contributionCount"]))
    t.append('<text class="m" x="40" y="282" font-size="12" letter-spacing="1.4" fill="%s">%s</text>' % (p["dim"], left))
    t.append('<text class="m" x="1240" y="282" font-size="12" letter-spacing="1.4" text-anchor="end" fill="%s">%s</text>' % (p["dim"], right))
    t.append("</svg>")
    return "".join(t)


if __name__ == "__main__":
    login, out_dir = sys.argv[1], sys.argv[2]
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN is not set")
    cal = fetch(login, token)
    if cal["totalContributions"] == 0 or not cal["weeks"]:
        raise SystemExit("Empty calendar; keeping the previous graph")
    font = base64.b64encode(open(os.path.join(ROOT, "assets", "fonts", "mono.woff2"), "rb").read()).decode()
    for name, palette in THEMES.items():
        with open(os.path.join(out_dir, name), "w") as fh:
            fh.write(render(cal, palette, font))
