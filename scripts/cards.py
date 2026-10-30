"""Build the project cards from the GitHub API, all with the same height.

The cards used to come from the public github-readme-stats instance, which went
down (DEPLOYMENT_PAUSED). They are now drawn here from assets/card-template.svg,
a copy of that service's tokyonight pin card pinned to 150px, so the README
doesn't depend on an outside service. The 42 logo replaces "42" in the
42CommonCore title. Which repos get a card is read from the README: to swap a
project, change its link and its assets/cards/<repo>.svg image there.
Run daily by .github/workflows/cards.yml.
"""
import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from github_api import USER, graphql

DESCRIPTION_WIDTH = 59  # characters per line, as github-readme-stats wraps them
DESCRIPTION_LINES = 3   # three lines is what fits in the 150px card
# Compact layout, shown when the card is drawn under 280px wide (phones)
COMPACT_DESCRIPTION_WIDTH = 28  # characters per line at 22px
COMPACT_DESCRIPTION_LINES = 2
COMPACT_TITLE_SCALE = 1.6
COMPACT_STATS_SCALE = 1.8
TITLE_MAX_WIDTH = 350  # room for the scaled title inside the 400px card

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
OUT_DIR = ROOT / "assets" / "cards"
TEMPLATE = ROOT / "assets" / "card-template.svg"
TILE = ROOT / "assets" / "42-tile.svg"

STAR_ICON = ("M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 "
             "4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 "
             "6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 "
             "0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 "
             "01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 "
             "01-.564-.41L8 2.694v.001z")
FORK_ICON = ("M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 "
             "005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 "
             "0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 "
             "11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z")

def readme_repos():
    """The README decides which cards exist: every assets/cards/<repo>.svg it shows."""
    repos = list(dict.fromkeys(re.findall(r'src="assets/cards/([\w.-]+)\.svg"', README.read_text())))
    if not repos:
        raise SystemExit("No assets/cards/<repo>.svg images found in README.md")
    return repos


def fetch_repos(repos):
    query = "query { user(login: \"%s\") { %s } }" % (USER, " ".join(
        f'r{i}: repository(name: "{repo}") '
        "{ name description stargazerCount forkCount primaryLanguage { name color } }"
        for i, repo in enumerate(repos)
    ))
    user = graphql(query)["user"]
    missing = [repo for i, repo in enumerate(repos) if user[f"r{i}"] is None]
    if missing:
        raise SystemExit(f"Repositories not found: {', '.join(missing)}")
    return [user[f"r{i}"] for i in range(len(repos))]


def description_tspans(description, width=DESCRIPTION_WIDTH, max_lines=DESCRIPTION_LINES):
    lines = textwrap.wrap(description or "No description provided", width)
    if len(lines) > max_lines:
        # Cut at a word, leaving room for the "..."
        last = textwrap.wrap(" ".join(lines[max_lines - 1:]), width - 3)[0]
        lines = lines[:max_lines - 1] + [last.rstrip(",;:") + "..."]
    return "".join(f'<tspan dy="1.2em" x="25">{escape(line)}</tspan>' for line in lines)


def stat_item(x, inner):
    return f'      <g transform="translate({x}, 0)">\n{inner}\n    </g>'


def counter(testid, icon, count):
    return (f'    <g data-testid="{testid}">\n'
            f'      <svg class="icon" y="-12" viewBox="0 0 16 16" width="16" height="16">'
            f'<path fill-rule="evenodd" d="{icon}"/></svg>\n'
            f'      <text class="gray" x="25">{count}</text>\n'
            f'    </g>')


def stats_row(repo):
    """Language, then stars and forks when they aren't zero, like the service did."""
    items, x = [], 0
    lang = repo["primaryLanguage"]
    if lang:
        items.append(stat_item(x, (
            '    <g data-testid="primary-lang">\n'
            f'      <circle data-testid="lang-color" cx="0" cy="-5" r="6" fill="{lang["color"]}" />\n'
            f'      <text data-testid="lang-name" class="gray" x="15">{escape(lang["name"])}</text>\n'
            '    </g>')))
        x += 15 + 7 * len(lang["name"]) + 20
    for testid, icon, count in (("stargazers", STAR_ICON, repo["stargazerCount"]),
                                ("forkcount", FORK_ICON, repo["forkCount"])):
        if count:
            items.append(stat_item(x, counter(testid, icon, count)))
            x += 25 + 7 * len(str(count)) + 20
    return "\n".join(items)


def compact_layout(repo, stats):
    """Same card with fewer, bigger words: the title (reused from the full layout
    and scaled up), two lines of description and the language row."""
    # The title is 18px bold, about 10px per character, after a 25px icon
    title_width = 25 + 10 * len(repo["name"])
    scale = min(COMPACT_TITLE_SCALE, TITLE_MAX_WIDTH / title_width)
    # The title group sits at (25, 35); move it so the scaled copy starts at (25, 42)
    dx, dy = 25 - 25 * scale, 42 - 35 * scale
    description = description_tspans(repo["description"],
                                     COMPACT_DESCRIPTION_WIDTH, COMPACT_DESCRIPTION_LINES)
    return (f'      <use href="#title" transform="translate({dx:g}, {dy:g}) scale({scale:g})" />\n'
            f'      <text class="description" x="25" y="50">{description}</text>\n'
            f'      <g transform="translate(30, 138) scale({COMPACT_STATS_SCALE:g})">\n'
            f'{stats}\n'
            f'      </g>')


def render(repo):
    stats = stats_row(repo)
    return TEMPLATE.read_text().format(
        name=escape(repo["name"]),
        description=description_tspans(repo["description"]),
        stats=stats,
        compact=compact_layout(repo, stats),
    )


def add_42_logo(svg):
    """Title '42CommonCore' becomes the 42 tile followed by 'CommonCore'."""
    tile = TILE.read_text()
    view_box = re.search(r'viewBox="([^"]+)"', tile).group(1)
    tile_inner = tile[tile.index(">") + 1:tile.rindex("</svg>")]
    title = re.search(r'<g transform="translate\(25, 0\)">\s*<text[^>]*>42CommonCore</text>\s*</g>', svg)
    if not title:
        raise SystemExit("42CommonCore title not found in card")
    new_title = (
        '<g transform="translate(25, 0)">'
        f'<svg x="0" y="-15" width="19" height="19" viewBox="{view_box}">{tile_inner}</svg>'
        '<text x="25" y="0" class="header" data-testid="header">CommonCore</text></g>'
    )
    return svg[:title.start()] + new_title + svg[title.end():]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    repos = readme_repos()
    # Files are saved under the name the README uses, whatever the repo's capitalization
    for file_name, repo in zip(repos, fetch_repos(repos)):
        if repo["name"] == "42CommonCore" and repo["description"]:
            # The description repeats "42" in plain text; the logo in the title already says it
            repo["description"] = repo["description"].replace(
                "my 42 Common Core projects at 42 Barcelona",
                "all my Common Core projects in Barcelona")
        svg = render(repo)
        if repo["name"] == "42CommonCore":
            svg = add_42_logo(svg)
        (OUT_DIR / f"{file_name}.svg").write_text(svg, encoding="utf-8")
        print(f"{file_name}: ok")


if __name__ == "__main__":
    main()
