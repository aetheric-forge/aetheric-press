name: Publish Aetheric Press
on:
  push:
    branches: [ main ]
    paths:
      - "articles/**"
      - "config.yml"
      - "scripts/build_rss.py"
      - "index.md"

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install pyyaml
      - name: Build RSS
        run: python scripts/build_rss.py
      - name: Commit feed
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            git config user.name "press-bot"
            git config user.email "press-bot@users.noreply.github.com"
            git add feed.xml index.md
            git commit -m "ci: regenerate feed"
            git push
          fi
