# Profile cards: how to use and customize them

These scripts draw the project cards, the GitHub stats card and the top languages card shown in the profile README. They run on GitHub Actions every day, using only the GitHub API: no external services, no accounts, no secrets to set up.

**The one thing to remember:** to choose which project cards appear, edit the main `README.md`. You never need to touch the scripts for that.

## Quick path: change which projects get a card

1. Open the main `README.md` (the one in the root of the repo, not this one).
2. Find the "Highlighted projects" block. Each card is one line like this:

   ```html
   <a href="https://github.com/petandk/webserv"><img width="49%" src="assets/cards/webserv.svg" alt="webserv"></a>
   ```

3. To **swap** a card, change the repo name in the three places on that line: the link, the `src` and the `alt`. To **add** one, copy a line and change it. To **remove** one, delete the line.
4. Commit and push.

That's it. The push starts the workflow, which builds any new card in about a minute. The cards appear in the same order as the lines in the README.

> **Use the exact repo name** in `src="assets/cards/<repo>.svg"`. If the name is wrong, the workflow fails with `Repositories not found: <name>`, and nothing gets overwritten.

## Use these scripts on your own profile

1. Copy these into your profile repo (the repo named exactly like your username):
   - `scripts/` (this folder)
   - `assets/card-template.svg`
   - `.github/workflows/cards.yml`
2. In `scripts/github_api.py`, change `USER = "petandk"` to your username.
3. In your `README.md`, add one line per project as shown in the quick path above, using your username in the link. For the stats cards, add:

   ```html
   <img height="190" src="assets/stats/stats.svg" alt="GitHub stats">
   <img height="190" src="assets/stats/top-langs.svg" alt="Top languages">
   ```

4. Push. Then check the **Actions** tab: the "Update project cards" run should be green.

## When do the cards update?

| What you do | What happens |
|---|---|
| Nothing | The workflow runs once a day and refreshes stars, descriptions and stats. It's scheduled for 00:30 UTC, but GitHub often starts scheduled runs a few hours late. |
| Push a change to `README.md`, a script, or the card template | The workflow runs right away. |
| Want it now, without changing anything | **Actions** tab → **Update project cards** → **Run workflow**. |

The workflow only makes a commit (`chore: update project cards`) when a card actually changed.

## Change the colors

All the colors are in **one place**: the `COLORS` block at the top of `scripts/cards.py`. Both the project cards and the stats cards use it.

```python
COLORS = {
    "background": "#1a1b27",   # card background (dark navy)
    "title_color": "#70a5fd",  # card titles (blue)
    "text_color": "#38bdae",   # descriptions, stats and language names (teal)
    "icon_color": "#bf91f3",   # icons: repo book, star, fork, commit... (purple)
}
```

1. Change the values you want. Any CSS color works: `"#ff0000"`, `"red"`, `"rgb(255, 0, 0)"`.
2. Commit and push. The workflow redraws every card with the new colors.

The language dots (C gray, C++ pink, and so on) use GitHub's official language colors. They come from the API, so they aren't in `COLORS`.

> **Editing `assets/card-template.svg` directly?** CSS braces in it are written doubled, like `.icon {{ fill: {icon_color} }}`. Keep them doubled. Single `{` and `}` mark the slots the script fills in, such as `{name}` or `{icon_color}`.

## Other settings

All of these are constants at the top of the scripts.

| Setting | File | What it does |
|---|---|---|
| `USER` | `github_api.py` | Whose repos and stats are shown. |
| `COLORS` | `cards.py` | Colors of all the cards (see "Change the colors"). |
| `DESCRIPTION_WIDTH`, `DESCRIPTION_LINES` | `cards.py` | Characters per line and number of lines of the description on a card. Longer descriptions end with `...`. |
| `COMPACT_*` | `cards.py` | Same idea, for the phone layout (see below). |
| `TOP_LANGUAGES` | `stats.py` | How many languages the top languages card lists. |
| `WIDTH`, `HEIGHT` | `stats.py` | Size of the two stats cards. If you change `HEIGHT`, change `height="190"` in the README too. |

## How it works (for the curious)

| File | Job |
|---|---|
| `cards.py` | Reads the `assets/cards/<repo>.svg` lines from `README.md`, asks the GitHub API for each repo's description, stars, forks and language, and fills `assets/card-template.svg` with them. |
| `stats.py` | Asks the API for your stars, commits, PRs, issues and languages, and draws `assets/stats/stats.svg` and `assets/stats/top-langs.svg`. |
| `github_api.py` | The small helper both scripts use to call the GitHub API. |

**Phone layout.** On a phone, two cards side by side are only about 175px wide, too small to read. Each card contains a second, simpler layout with bigger text, and switches to it by itself when it is drawn under 280px wide (the `@media (max-width: 280px)` rule in the template). Desktop is not affected.

**Only public data.** Stats count public repositories and public activity only, because the workflow's token can't see private ones.

**The 42 logo.** A repo named exactly `42CommonCore` gets the 42 logo in its title and a slightly reworded description. It's specific to this profile; for any other repo name the code does nothing, so you can leave it.

## Try it on your computer (optional)

You need Python 3 and the [GitHub CLI](https://cli.github.com/) logged in (`gh auth login`). From the root of the repo:

```bash
GITHUB_TOKEN="$(gh auth token)" python3 scripts/cards.py
GITHUB_TOKEN="$(gh auth token)" python3 scripts/stats.py
```

Then open the `.svg` files in `assets/cards/` and `assets/stats/` in your browser.

> Your personal token can see your **private** repos, so the stats can show higher numbers locally than on GitHub. That's expected: the next workflow run puts back the public-only numbers.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Red run with `Repositories not found: X` | A repo name in the README is wrong. Check spelling and capitalization in `src="assets/cards/X.svg"`. |
| Red run with `No assets/cards/<repo>.svg images found` | The README has no card lines, or they don't follow the format in the quick path. |
| Red run failing at `git push` | The workflow can't write to the repo. Check that `.github/workflows/cards.yml` still has `permissions: contents: write`. |
| No runs at all in the **Actions** tab | Actions may be turned off for the repo: **Settings → Actions → General → Allow all actions**. |
| A card shows as a broken image | The workflow hasn't built it yet. Wait for the run to finish, or start one from the **Actions** tab. |
| The README still shows the old card after a green run | GitHub caches images for a few minutes. Reload later. |
