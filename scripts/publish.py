#!/usr/bin/env python3
import subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_rss.py")])
subprocess.check_call(["git","add","."])
subprocess.check_call(["git","commit","-m","chore: publish feed + articles"])
subprocess.check_call(["git","push"])
