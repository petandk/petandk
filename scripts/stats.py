"""Build the GitHub stats and top languages cards from the GitHub API.

They replace the github-readme-stats images, whose public instance went down
(DEPLOYMENT_PAUSED). Same tokyonight colors as the project cards. Only public
repositories count, as before. Run daily by .github/workflows/cards.yml.
"""
from pathlib import Path
from xml.sax.saxutils import escape

from cards import COLORS, STAR_ICON
from github_api import USER, graphql

WIDTH, HEIGHT = 400, 190
TOP_LANGUAGES = 6

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "stats"

QUERY = """query { user(login: "%s") {
  name
  contributionsCollection { totalCommitContributions }
  pullRequests { totalCount }
  issues { totalCount }
  repositoriesContributedTo(contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) { totalCount }
  repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
    nodes { stargazerCount
      languages(first: 20, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
  }
} }""" % USER

# Octicons, 16x16
COMMIT_ICON = ("M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 "
               "0h3.32a.75.75 0 010 1.5zm-1.43-.75a2.5 2.5 0 10-5 0 2.5 2.5 0 005 0z")
PR_ICON = ("M1.5 3.25a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 "
           "3.25zm5.677-.177L9.573.677A.25.25 0 0110 .854V2.5h1A2.5 2.5 0 0113.5 5v5.628a2.251 2.251 "
           "0 11-1.5 0V5a1 1 0 00-1-1h-1v1.646a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 "
           "2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm0 9.5a.75.75 0 100 1.5.75.75 0 000-1.5zm8.25.75a.75.75 "
           "0 101.5 0 .75.75 0 00-1.5 0z")
ISSUE_ICON = ("M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 "
              "1113 0 6.5 6.5 0 01-13 0z")
REPO_ICON = ("M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 "
             "110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 "
             "0-.694.074-1 .208V2.5a1 1 0 011-1h8z")

CARD = """<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="titleId">
  <title id="titleId">{title}</title>
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; }}
    .stat {{ font: 600 14px 'Segoe UI', Ubuntu, "Helvetica Neue", Sans-Serif; fill: {text_color}; }}
    .lang {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
    .icon {{ fill: {icon_color}; }}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="{w1}" height="{h1}" fill="{background}" />
  <text x="25" y="38" class="header">{title}</text>
{body}
</svg>
"""


def card(title, body):
    return CARD.format(w=WIDTH, h=HEIGHT, w1=WIDTH - 1, h1=HEIGHT - 1, title=escape(title), body=body,
                       **COLORS)


def stats_card(user):
    stars = sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])
    rows = [
        (STAR_ICON, "Total Stars Earned", stars),
        (COMMIT_ICON, "Total Commits (last year)", user["contributionsCollection"]["totalCommitContributions"]),
        (PR_ICON, "Total PRs", user["pullRequests"]["totalCount"]),
        (ISSUE_ICON, "Total Issues", user["issues"]["totalCount"]),
        (REPO_ICON, "Contributed to (last year)", user["repositoriesContributedTo"]["totalCount"]),
    ]
    body = "\n".join(
        f'  <g transform="translate(25, {68 + 25 * i})">'
        f'<svg class="icon" y="-13" viewBox="0 0 16 16" width="16" height="16">'
        f'<path fill-rule="evenodd" d="{icon}"/></svg>'
        f'<text x="25" class="stat">{label}:</text>'
        f'<text x="{WIDTH - 50}" class="stat" text-anchor="end">{value:,}</text></g>'
        for i, (icon, label, value) in enumerate(rows)
    )
    name = user["name"] or USER
    return card(f"{name}'s GitHub Stats", body)


def languages_card(user):
    totals = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            lang = edge["node"]
            size, _ = totals.get(lang["name"], (0, lang["color"]))
            totals[lang["name"]] = (size + edge["size"], lang["color"] or "#858585")
    top = sorted(totals.items(), key=lambda item: -item[1][0])[:TOP_LANGUAGES]
    shown = sum(size for _, (size, _) in top)

    bar_width, x, segments, legend = WIDTH - 50, 25.0, [], []
    for i, (name, (size, color)) in enumerate(top):
        share = size / shown
        segments.append(f'    <rect x="{x:.2f}" y="0" width="{share * bar_width:.2f}" height="8" fill="{color}" />')
        x += share * bar_width
        col, row = i % 2, i // 2
        legend.append(
            f'  <g transform="translate({25 + col * 175}, {100 + row * 28})">'
            f'<circle cx="5" cy="-5" r="5" fill="{color}" />'
            f'<text x="17" class="lang">{escape(name)} {share * 100:.2f}%</text></g>')
    bar = ('  <mask id="bar"><rect x="25" y="0" width="%d" height="8" rx="4" fill="white" /></mask>\n'
           '  <g transform="translate(0, 60)" mask="url(#bar)">\n%s\n  </g>' % (bar_width, "\n".join(segments)))
    return card("Most Used Languages", bar + "\n" + "\n".join(legend))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    user = graphql(QUERY)["user"]
    (OUT_DIR / "stats.svg").write_text(stats_card(user), encoding="utf-8")
    (OUT_DIR / "top-langs.svg").write_text(languages_card(user), encoding="utf-8")
    print("stats: ok")


if __name__ == "__main__":
    main()
