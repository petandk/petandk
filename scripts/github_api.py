"""Minimal GitHub GraphQL client shared by the card scripts."""
import json
import os
import urllib.request

USER = "petandk"


def graphql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "User-Agent": f"{USER}-profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        body = json.load(response)
    if body.get("errors"):
        raise SystemExit(f"GitHub API error: {body['errors']}")
    return body["data"]
