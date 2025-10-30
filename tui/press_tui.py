#!/usr/bin/env python3
import os, subprocess, datetime, re, sys, shutil, yaml
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static, Label

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"

TEMPLATE = """---
title: "{title}"
date: {date}
author: "{author}"
tags: [{tags}]
summary: "{summary}"
slug: "{slug}"
draft: false
---
"""

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9-]+","-", s.lower()).strip("-")

class PressApp(App):
    CSS = "Screen {align: center middle;}"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Aetheric Press — New Article")
        self.title = Input(placeholder="Title")
        self.summary = Input(placeholder="One-sentence summary")
        self.tags = Input(placeholder="comma,separated,tags")
        yield self.title
        yield self.summary
        yield self.tags
        yield Button("Create & Edit", id="create", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "create":
            return
        cfg = yaml.safe_load((ROOT / "config.yml").read_text())
        title = self.title.value.strip()
        dt = datetime.datetime.now().astimezone()
        slug = f"{dt.date()}-{slugify(title)}"
        path = ARTICLES / f"{slug}.md"
        fm = TEMPLATE.format(
            title=title,
            date=dt.isoformat(),
            author=cfg.get("author","Valkyr"),
            tags=", ".join([f'"{t.strip()}"' for t in self.tags.value.split(",") if t.strip()]),
            summary=self.summary.value.replace('"', '\\"'),
            slug=slugify(title),
        )
        path.write_text(fm, encoding="utf-8")
        editor = os.environ.get("EDITOR","nano")
        subprocess.call([editor, str(path)])
        # After save, rebuild feed
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_rss.py")])
        self.exit()

if __name__ == "__main__":
    # ensure structure
    ARTICLES.mkdir(exist_ok=True, parents=True)
    PressApp().run()
