"""
Build a SINGLE-FILE, self-extracting bundle of the whole codebase.

    python tools/make_bundle.py

Produces two artefacts in dist/ — pick whichever your network will let through:

  1. regcompliance_bundle.py   ONE Python file. Paste it anywhere (email, Teams, Confluence,
                               a Topaz upload box, a text field). Run it:

                                   python regcompliance_bundle.py

                               and it writes the entire project back out to disk, verifies every
                               file against a SHA-256 checksum, and tells you what to do next.

  2. CODE_BUNDLE.md            The same code as readable Markdown, every file in a fenced block.
                               For pasting into a wiki, a Word doc, or a review that has to be
                               read by a human rather than executed.

WHY THIS EXISTS
GitHub is blocked and zip attachments are not allowed. Neither of those is a reason to hand over a
partial codebase. `api.py` alone imports ten other files and will not even start on its own — a
"here are the three important files" handover would leave the receiving team with a contract to
nothing.

So the constraint is: everything must travel as TEXT, in ONE artefact. That is what this builds.

INTEGRITY MATTERS MORE THAN CONVENIENCE
Text that crosses an email client, a corporate proxy and a paste buffer gets mangled — trailing
whitespace stripped, line endings rewritten, the odd character eaten. A bundle that silently drops a
line of the provenance verifier is worse than no bundle, because nobody would notice.
So every file carries a SHA-256, and the extractor REFUSES to write a file whose hash does not match.
"""

import base64
import hashlib
import json
import os
import pathlib
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# ---------------------------------------------------------------------------------------------
# What travels.
#
# The Streamlit UI is deliberately EXCLUDED: React replaces it, so shipping it would only invite
# somebody to port a screen we are throwing away. Everything else is mandatory — the agents ARE the
# product, and api.py is a thin wrapper that does nothing without them.
# ---------------------------------------------------------------------------------------------
INCLUDE = [
    # --- the product: agents + core. Nothing works without these. ---
    "agents/__init__.py",
    "agents/regulatory_monitor/__init__.py",
    "agents/regulatory_monitor/graph.py",          # <-- contains the provenance verifier
    "agents/regulatory_monitor/tools.py",
    "agents/obligation_impact/__init__.py",
    "agents/obligation_impact/graph.py",
    "agents/audit_prep/__init__.py",
    "agents/audit_prep/graph.py",
    "agents/case_analytics/__init__.py",
    "agents/case_analytics/chain.py",
    "core/__init__.py",
    "core/prompts.py",
    "core/domains.py",
    "core/llm.py",
    "core/vectorstore.py",
    "core/db.py",
    "core/embeddings.py",
    # --- the REST seam React codes against ---
    "api.py",
    "requirements.txt",
    ".env.example",
    # --- the documents ---
    "BLUEPRINT.md",
    "TOPAZ_PORT.md",
    "docs/openapi.json",
]

# The one file whose loss would be silent and catastrophic.
CRITICAL = "agents/regulatory_monitor/graph.py"


def collect() -> dict[str, dict]:
    files = {}
    for rel in INCLUDE:
        p = ROOT / rel
        if not p.exists():
            raise SystemExit(f"MISSING: {rel} — refusing to build an incomplete bundle")
        raw = p.read_bytes()
        files[rel] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "b64": base64.b64encode(zlib.compress(raw, 9)).decode("ascii"),
        }
    return files


EXTRACTOR = '''#!/usr/bin/env python3
"""
Regulatory Compliance AI — SELF-EXTRACTING BUNDLE
=================================================

The entire codebase, as one text file. No zip. No GitHub. No network.

    python regcompliance_bundle.py                 # extracts to ./regcompliance/
    python regcompliance_bundle.py --out /some/dir # or wherever
    python regcompliance_bundle.py --list          # show contents without writing anything

Every file is verified against a SHA-256 checksum on the way out. If a paste buffer, an email
client or a corporate proxy has mangled so much as one character, extraction FAILS LOUDLY rather
than writing a subtly corrupt file.

That matters here more than it usually would: this bundle contains a provenance verifier whose whole
job is to stop an AI inventing a regulatory obligation. A version of it that was quietly corrupted in
transit would still run — and would silently stop verifying. So we check.
"""

import argparse
import base64
import hashlib
import json
import pathlib
import sys
import zlib

# __PAYLOAD__

try:
    MANIFEST = json.loads(zlib.decompress(base64.b64decode(_MANIFEST_B64)).decode("utf-8"))
except Exception as _e:
    # The payload itself was mangled in transit. Say so in words a human can act on, rather than
    # dumping a zlib traceback that looks like a bug in this script.
    print("=" * 74)
    print("BUNDLE CORRUPTED IN TRANSIT — the embedded payload will not decode.")
    print("=" * 74)
    print(f"\\n  ({type(_e).__name__}: {_e})\\n")
    print("This file was altered between being generated and being run. The usual causes:")
    print("  - an email client or chat app rewrote line endings or wrapped long lines")
    print("  - a paste buffer truncated the file (check the end of the payload is intact)")
    print("  - the file was saved with a different encoding\\n")
    print("FIX: re-send it as a plain-text file attachment, or through a channel that does")
    print("     not rewrite content. Do NOT try to repair it by hand.")
    sys.exit(2)

CRITICAL = "__CRITICAL__"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="regcompliance")
    ap.add_argument("--list", action="store_true", help="show contents, write nothing")
    args = ap.parse_args()

    files = MANIFEST["files"]

    if args.list:
        print(f"{MANIFEST['name']}  ·  {len(files)} files  ·  {MANIFEST['total_bytes']:,} bytes\\n")
        for rel, m in files.items():
            flag = "  <-- THE PROVENANCE VERIFIER" if rel == CRITICAL else ""
            print(f"  {m['bytes']:>7,}  {rel}{flag}")
        return 0

    out = pathlib.Path(args.out)
    print(f"Extracting {len(files)} files to {out.resolve()}\\n")

    bad = []
    for rel, m in files.items():
        raw = zlib.decompress(base64.b64decode(m["b64"]))
        got = hashlib.sha256(raw).hexdigest()
        if got != m["sha256"]:
            bad.append(rel)
            print(f"  CORRUPT  {rel}")
            print(f"           expected {m['sha256'][:16]}...  got {got[:16]}...")
            continue
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(raw)
        mark = "  <-- provenance verifier" if rel == CRITICAL else ""
        print(f"  ok  {m['bytes']:>7,}  {rel}{mark}")

    if bad:
        print(f"\\n{'=' * 74}")
        print(f"EXTRACTION FAILED — {len(bad)} file(s) corrupted in transit:")
        for b in bad:
            print(f"  x  {b}")
        print("\\nThe text was mangled somewhere between here and there — most likely by an email")
        print("client rewriting line endings, or a paste buffer eating characters.")
        print("DO NOT USE THIS EXTRACTION. Re-send the bundle as a plain-text attachment,")
        print("or through a channel that does not rewrite content.")
        print("=" * 74)
        return 1

    print(f"\\n{'=' * 74}")
    print(f"ALL {len(files)} FILES VERIFIED against SHA-256. Nothing was corrupted in transit.")
    print("=" * 74)
    print(f"""
NEXT STEPS

  cd {args.out}
  pip install -r requirements.txt
  cp .env.example .env          # add OPENAI_API_KEY

  uvicorn api:app --reload --port 8000
  open http://localhost:8000/docs

THEN, IN THE REACT PROJECT

  npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts

  -> a fully typed client, generated from the real code. It cannot drift from it.

READ FIRST
  TOPAZ_PORT.md   how to port this to React on Topaz, and the TWO things the UI must get right
  BLUEPRINT.md    what the system is: 7 agents, 4 workflows, the trust architecture

THE ONE THING NOT TO LOSE
  agents/regulatory_monitor/graph.py contains _quote_in_source() — the provenance verifier.
  It is CODE, not a prompt: it checks that an obligation's quote really appears in the source
  regulation, and flags it when it does not. It is the reason this system is safe to put in front
  of a regulated utility. If it is dropped in the port, the app will still run — and will silently
  start letting an AI invent regulatory deadlines into a compliance register.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def build():
    DIST.mkdir(exist_ok=True)
    files = collect()
    total = sum(f["bytes"] for f in files.values())

    manifest = {
        "name": "Regulatory Compliance AI (PG&E)",
        "files": files,
        "total_bytes": total,
    }
    payload = base64.b64encode(
        zlib.compress(json.dumps(manifest).encode("utf-8"), 9)
    ).decode("ascii")

    # Wrap the payload so no single line is absurdly long — some mail clients hard-wrap.
    lines = [payload[i:i + 76] for i in range(0, len(payload), 76)]
    embedded = '_MANIFEST_B64 = (\n    "' + '"\n    "'.join(lines) + '"\n)\n\n'

    assert "# __PAYLOAD__" in EXTRACTOR, "payload placeholder missing from template"
    script = EXTRACTOR.replace("# __PAYLOAD__", embedded.rstrip(), 1)
    script = script.replace('CRITICAL = "__CRITICAL__"', f'CRITICAL = {CRITICAL!r}')

    out_py = DIST / "regcompliance_bundle.py"
    out_py.write_text(script, encoding="utf-8", newline="\n")

    # --- readable Markdown variant, for a wiki or a human reviewer ---
    md = [
        "# Regulatory Compliance AI — Full Source Bundle",
        "",
        "> Every file below. Paste-safe, human-readable. For the executable version that",
        "> reconstitutes the project with checksums, use `regcompliance_bundle.py`.",
        "",
        f"**{len(files)} files · {total:,} bytes**",
        "",
        "## Contents",
        "",
    ]
    for rel, m in files.items():
        flag = "  ← **the provenance verifier — do not lose this**" if rel == CRITICAL else ""
        md.append(f"- `{rel}` ({m['bytes']:,} bytes){flag}")
    md.append("")
    md.append("---")
    md.append("")

    for rel in files:
        lang = {"py": "python", "json": "json", "md": "markdown",
                "txt": "text", "example": "bash"}.get(rel.rsplit(".", 1)[-1], "text")
        body = (ROOT / rel).read_text(encoding="utf-8")
        md.append(f"## `{rel}`")
        md.append("")
        md.append(f"```{lang}")
        md.append(body.rstrip())
        md.append("```")
        md.append("")

    out_md = DIST / "CODE_BUNDLE.md"
    out_md.write_text("\n".join(md), encoding="utf-8", newline="\n")

    print(f"BUILT  {out_py}   {out_py.stat().st_size:>9,} bytes  ({len(files)} files, self-verifying)")
    print(f"BUILT  {out_md}   {out_md.stat().st_size:>9,} bytes  (readable markdown)")
    print(f"\nSource payload: {total:,} bytes  ->  bundle {out_py.stat().st_size:,} bytes")
    return out_py


if __name__ == "__main__":
    build()
