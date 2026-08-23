#!/usr/bin/env python3
"""Drift check for the Easy2257 MCP listing.

Why this exists
---------------
The same handful of facts about this server are written down in six places:
this repo's server.json, the row the official registry serves, the app's
/.well-known/mcp/server.json, the two OAuth discovery documents, and the prose
on llms.txt, /ai-assistant and the docs site. On 2026-08-23 two of those
disagreed about the server's own name for several hours, and a person reading
found it, not a check. That is what this script is for.

It reads only public URLs. It never holds a credential. An ez_mcp_ key sitting
in Actions would be a rotating liability and a read path into producer
compliance state, so the price of that is: this script can never call a tool,
only the unauthenticated refusal.

What it deliberately does NOT do
--------------------------------
No whole-document diffs (the registry row carries a _meta block nothing else
emits, the app copy carries no $schema, key order differs everywhere: a
document diff fires on day one and gets muted by Friday). No rendered HTML
comparison (class names and script hashes move every deploy). No prose
equivalence between surfaces written for different readers. No uptime or
latency: there is already a canary lane for that.

Usage:  python scripts/check-listing.py [--repo-only]
        --repo-only relaxes the checks that are legitimately allowed to lag
        while the repo sits ahead of an unpublished registry row.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REGISTRY_SEARCH = (
    "https://registry.modelcontextprotocol.io/v0/servers"
    "?search=io.github.Agaveis/easy2257-mcp&version=latest"
)
WELL_KNOWN = "https://easy2257.com/.well-known/mcp/server.json"
PROTECTED_RESOURCE = "https://easy2257.com/.well-known/oauth-protected-resource"
LLMS_TXT = "https://easy2257.com/llms.txt"
AI_ASSISTANT = "https://easy2257.com/ai-assistant"
DOCS_PAGE = "https://docs.easy2257.com/docs/ai-assistant"

TIMEOUT = 30
RETRIES = 3

hard: list[str] = []
warn: list[str] = []
unreachable: list[str] = []


def fetch(url: str, method: str = "GET", body: bytes | None = None,
          headers: dict[str, str] | None = None):
    """Return (status, body_text, headers) or None if the host stayed down.

    A host that is still unreachable after retries is NOT a drift failure. It
    is a network problem, and failing the job for it is how a check earns the
    mute button.
    """
    last = None
    for attempt in range(RETRIES):
        req = urllib.request.Request(url, method=method, data=body,
                                     headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
        except urllib.error.HTTPError as e:
            # An HTTP status IS an answer. 401 is the expected one below.
            return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)
        except Exception as e:  # noqa: BLE001 - any transport failure retries
            last = e
    unreachable.append(f"{url} ({last})")
    return None


def as_json(payload):
    try:
        return json.loads(payload)
    except Exception:
        return None


def main() -> int:
    repo_only = "--repo-only" in sys.argv

    local = json.loads((REPO / "server.json").read_text(encoding="utf-8"))

    # ---- gather -----------------------------------------------------------
    reg_row = None
    r = fetch(REGISTRY_SEARCH)
    if r and r[0] == 200:
        servers = (as_json(r[1]) or {}).get("servers") or []
        if servers:
            reg_row = servers[0]
        else:
            hard.append("registry returned no row for io.github.Agaveis/easy2257-mcp")
    elif r:
        hard.append(f"registry search answered {r[0]}")

    app_doc = None
    r = fetch(WELL_KNOWN)
    if r and r[0] == 200:
        app_doc = as_json(r[1])
        if app_doc is None:
            hard.append(f"{WELL_KNOWN} did not parse as JSON")
    elif r:
        hard.append(f"{WELL_KNOWN} answered {r[0]}")

    reg = (reg_row or {}).get("server") or {}
    copies = {"repo": local, "registry": reg, "app": app_doc or {}}
    present = {k: v for k, v in copies.items() if v}

    def field(doc: dict, path: str):
        if path == "remote_url":
            remotes = doc.get("remotes") or []
            return remotes[0].get("url") if remotes else None
        return doc.get(path)

    def compare(path: str, bucket: list[str], label: str):
        vals = {k: field(v, path) for k, v in present.items()}
        distinct = {json.dumps(v, sort_keys=True) for v in vals.values()}
        if len(distinct) > 1:
            bucket.append(f"{label} disagrees across copies: " +
                          ", ".join(f"{k}={v!r}" for k, v in vals.items()))

    # ---- 1, 2, 3: the three copies must agree on identity -----------------
    compare("remote_url", hard, "remotes[0].url")
    compare("name", hard, "name")
    # version is the field designed to move. While the repo sits ahead of an
    # unpublished row that is correct, not broken, so a push run only warns.
    compare("version", warn if repo_only else hard, "version")
    compare("description", warn, "description")
    compare("title", warn, "title")

    desc = local.get("description", "")
    if len(desc) > 100:
        hard.append(f"server.json description is {len(desc)} chars, the schema caps it at 100")

    # ---- 1 (cont): the endpoint the OAuth layer protects is the same one ---
    prm = None
    r = fetch(PROTECTED_RESOURCE)
    if r and r[0] == 200:
        prm = as_json(r[1])
    elif r:
        hard.append(f"{PROTECTED_RESOURCE} answered {r[0]}")

    local_url = field(local, "remote_url")
    if prm and prm.get("resource") != local_url:
        hard.append(f"protected-resource 'resource' is {prm.get('resource')!r}, "
                    f"server.json advertises {local_url!r}")

    # ---- 4: the refusal shape ---------------------------------------------
    init = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "drift-check", "version": "1"}},
    }).encode()
    r = fetch(local_url, method="POST", body=init, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    if r:
        status, _, hdrs = r
        if status == 200:
            hard.append("SECURITY: unauthenticated initialize returned 200. "
                        "The endpoint stopped requiring a credential.")
        elif status != 401:
            hard.append(f"unauthenticated initialize returned {status}, expected 401")
        challenge = next((v for k, v in hdrs.items()
                          if k.lower() == "www-authenticate"), None)
        if not challenge:
            hard.append("no WWW-Authenticate on the 401: sign-in clients cannot "
                        "discover how to authenticate")
        else:
            m = re.search(r'resource_metadata="([^"]+)"', challenge)
            if not m:
                hard.append(f"WWW-Authenticate carries no resource_metadata: {challenge!r}")
            else:
                rm = fetch(m.group(1))
                if rm and (rm[0] != 200 or as_json(rm[1]) is None):
                    hard.append(f"resource_metadata {m.group(1)} answered {rm[0]} "
                                "or did not parse")

    # ---- 5: the OAuth chain closes ----------------------------------------
    if prm:
        servers = prm.get("authorization_servers") or []
        if not servers:
            hard.append("protected-resource lists no authorization_servers")
        else:
            origin = servers[0].rstrip("/")
            r = fetch(f"{origin}/.well-known/oauth-authorization-server")
            if r and r[0] == 200:
                asm = as_json(r[1]) or {}
                if asm.get("issuer", "").rstrip("/") != origin:
                    hard.append(f"authorization-server issuer {asm.get('issuer')!r} "
                                f"does not match {origin!r}")
                if asm.get("scopes_supported") != ["mcp:read"]:
                    hard.append("authorization-server scopes_supported is "
                                f"{asm.get('scopes_supported')!r}, expected ['mcp:read']. "
                                "Three prose surfaces say 'the single scope'.")
                # ---- 7: one documentation URL, and it resolves -------------
                docs = {
                    "server.json websiteUrl": local.get("websiteUrl"),
                    "protected-resource resource_documentation": prm.get("resource_documentation"),
                    "authorization-server service_documentation": asm.get("service_documentation"),
                }
                if len({v for v in docs.values() if v}) > 1:
                    hard.append("documentation URL disagrees: " +
                                ", ".join(f"{k}={v!r}" for k, v in docs.items()))
                target = local.get("websiteUrl")
                if target:
                    d = fetch(target)
                    if d and d[0] != 200:
                        hard.append(f"{target} answered {d[0]}")
            elif r:
                hard.append(f"{origin}/.well-known/oauth-authorization-server "
                            f"answered {r[0]}")
        if prm.get("scopes_supported") != ["mcp:read"]:
            hard.append("protected-resource scopes_supported is "
                        f"{prm.get('scopes_supported')!r}, expected ['mcp:read']")

    # ---- 6: the row is actually listed ------------------------------------
    if reg_row:
        meta = (reg_row.get("_meta") or {}).get(
            "io.modelcontextprotocol.registry/official") or {}
        if meta.get("status") != "active":
            hard.append(f"registry row status is {meta.get('status')!r}, not 'active'")
        if meta.get("isLatest") is not True:
            hard.append("registry row is not isLatest: a newer version is being served")

    # ---- 8: the legal-claim tripwire --------------------------------------
    #
    # 18 U.S.C. 2257 and 28 CFR 75.2 require an examined identity record. A
    # model release is a CARD-NETWORK obligation (Mastercard AN 5196, Visa
    # VIRP), not a federal one. On 2026-08-23 the product asserted otherwise on
    # three separate surfaces and each one was caught by a person. There is no
    # window in which that sentence is briefly correct, so this is hard.
    REQUIRING = r"(requires?|required|mandates?|mandated|obligat\w*)"
    TRIPWIRES = [
        (re.compile(rf"2257.{{0,80}}{REQUIRING}.{{0,80}}release", re.I | re.S),
         "text ties 2257 to a required release"),
        (re.compile(rf"release.{{0,60}}{REQUIRING}.{{0,60}}2257", re.I | re.S),
         "text ties a required release to 2257"),
        (re.compile(r"Required by 18 U\.S\.C\. 2257.*MODEL_RELEASE|"
                    r"MODEL_RELEASE.*Required by 18 U\.S\.C\. 2257", re.I),
         "the literal app-side defect string"),
    ]
    # PROJ- is not a real prefix: production codes are PROD-YYYY-NNN and scene
    # codes are that with PROD- swapped for SCENE-. Cheap regression guard.
    PROBES = [
        (re.compile(r"\bPROJ-"), "PROJ- is not a real code prefix, use PROD-"),
        (re.compile(r"Agave Information Solutions", re.I),
         "operator entity: the product elsewhere says it was never this entity"),
    ]

    def scan(name: str, text: str, hard_patterns, warn_patterns):
        stripped = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text,
                          flags=re.S | re.I)
        stripped = re.sub(r"<[^>]+>", " ", stripped)
        for rx, why in hard_patterns:
            m = rx.search(stripped)
            if m:
                hard.append(f"{name}: {why} -> {m.group(0)[:120]!r}")
        for rx, why in warn_patterns:
            m = rx.search(stripped)
            if m:
                warn.append(f"{name}: {why} -> {m.group(0)[:120]!r}")

    for md in sorted(REPO.glob("**/*.md")):
        if ".git" in md.parts:
            continue
        scan(str(md.relative_to(REPO)), md.read_text(encoding="utf-8"),
             TRIPWIRES, PROBES)

    for label, url in (("llms.txt", LLMS_TXT), ("/ai-assistant", AI_ASSISTANT),
                       ("docs ai-assistant", DOCS_PAGE)):
        if repo_only:
            continue
        r = fetch(url)
        if r and r[0] == 200:
            scan(label, r[1], TRIPWIRES, PROBES)
            if local_url and local_url not in r[1]:
                warn.append(f"{label} does not mention {local_url}")
        elif r:
            warn.append(f"{url} answered {r[0]}")

    # ---- report -----------------------------------------------------------
    for u in unreachable:
        print(f"::warning::unreachable after {RETRIES} tries, not treated as drift: {u}")
    for w in warn:
        print(f"::warning::{w}")
    for h in hard:
        print(f"::error::{h}")

    if hard:
        print(f"\nFAIL: {len(hard)} hard, {len(warn)} warnings")
        return 1
    print(f"\nOK: no drift. {len(warn)} warnings, {len(unreachable)} unreachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
