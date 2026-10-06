"""Download the project cards from github-readme-stats and give them all the same height.

The service sizes each card by how many lines its description takes (120, 140 or
150px), so cards side by side don't line up. This script pins every card to
CARD_HEIGHT, keeps the language row at the bottom, and puts the 42 logo in the
42CommonCore title. Run daily by .github/workflows/cards.yml.
"""
import re
import urllib.request
from pathlib import Path

USER = "petandk"
REPOS = ["42CommonCore", "ft_transcendence", "webserv", "minishell", "cub3d", "inception"]
CARD_URL = ("https://github-readme-stats.vercel.app/api/pin/"
            "?username={user}&repo={repo}&theme=tokyonight&hide_border=true")
CARD_HEIGHT = 150
LANG_ROW_FROM_BOTTOM = 75  # the service always places the language row 75px above the bottom

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "cards"
TILE = ROOT / "assets" / "42-tile.svg"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER}-profile-cards"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8")


def set_height(svg):
    tag = re.search(r"<svg\b[^>]*>", svg, re.S)
    old_height = int(re.search(r'height="(\d+)"', tag.group(0)).group(1))
    new_tag = re.sub(r'height="\d+"', f'height="{CARD_HEIGHT}"', tag.group(0), count=1)
    new_tag = re.sub(r'viewBox="0 0 (\d+) \d+"', rf'viewBox="0 0 \1 {CARD_HEIGHT}"', new_tag, count=1)
    svg = svg[:tag.start()] + new_tag + svg[tag.end():]
    old_row = old_height - LANG_ROW_FROM_BOTTOM
    new_row = CARD_HEIGHT - LANG_ROW_FROM_BOTTOM
    return svg.replace(f'<g transform="translate(30, {old_row})">',
                       f'<g transform="translate(30, {new_row})">', 1)


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
    svg = svg[:title.start()] + new_title + svg[title.end():]
    # The description repeats "42" in plain text; the logo in the title already says it
    return svg.replace("Entry point to my 42 Common Core projects at 42 Barcelona,",
                       "Entry point to all my Common Core projects in Barcelona,")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for repo in REPOS:
        svg = fetch(CARD_URL.format(user=USER, repo=repo))
        if 'data-testid="header"' not in svg:
            raise SystemExit(f"{repo}: unexpected response, keeping the previous card")
        svg = set_height(svg)
        if repo == "42CommonCore":
            svg = add_42_logo(svg)
        (OUT_DIR / f"{repo}.svg").write_text(svg, encoding="utf-8")
        print(f"{repo}: ok")


if __name__ == "__main__":
    main()
