# easy2257-mcp: the Easy2257 MCP connector

This repository is the public listing for the Easy2257 [Model Context
Protocol](https://modelcontextprotocol.io) server. The server itself is hosted
by Easy2257 and reached over the network, so there is nothing here to install
and no engine source: this repo holds the registry metadata, the privacy
statement, and the setup notes.

**Endpoint:** `https://easy2257.com/api/mcp` (Streamable HTTP)
**Setup and screenshots:** <https://easy2257.com/ai-assistant>

This connector reads one account's own compliance state. It is not the Easy2257
Partner API, which is the separate integration surface a platform uses to
receive compliance events.

Easy2257 keeps 18 U.S.C. 2257 records for adult content producers: who was in a
scene, that their identity was verified, which paperwork is signed, and a
certificate proving the record existed at a point in time. This connector lets
the AI assistant you already use read that compliance state and answer in plain
language.

MCP is an open, vendor-neutral standard, so one connection serves any MCP
client: Claude Code, Claude on the web and desktop, ChatGPT, Cursor, VS Code
with Copilot, Windsurf, Gemini CLI, Codex CLI, and others.

## Read-only, and narrow on purpose

The connection reports state. It cannot create a scene, change a record, sign
anything, attest to anything, or spend money. Paid actions and attestations
happen at easy2257.com, by a person, on purpose.

What comes back is compliance state: ids, public codes (`SCENE-`, `PROD-`,
`LOG-`), statuses, counts, dates, integrity hashes, and the short titles you
wrote yourself, returned only to the account that owns them. It never returns a
performer's name, date of birth, ID number, image, file path, address, or the
contents of anyone's document: those columns are not selected. That is a
deliberate boundary, not a gap, and it is what makes this surface safe to point
a shared assistant at.

Three guarantees, restated plainly:

- **It only reads.** No tool creates, changes, signs, or deletes a record.
- **No identity data crosses the wire.** Statuses, codes, counts, dates,
  integrity hashes, and your own titles only.
- **No money moves.** No tool touches checkout, scene activation, or any paid
  action.

## Connecting

Two ways in. Both land on the same read-only view of your own records, and the
tools cannot tell them apart.

### Sign in (no key to copy)

For ChatGPT, Claude on the web and desktop, and any assistant with a connectors
or integrations screen: add a custom connector pointing at
`https://easy2257.com/api/mcp`. The assistant sends you to Easy2257, you sign
in, and you approve read-only access. The assistant never sees a password or a
key. OAuth 2.1 with PKCE; the single scope is `mcp:read`.

### Paste a key

For Claude Code, Cursor, VS Code with Copilot, Windsurf, Gemini CLI, Codex CLI,
and anything else that lets you set a connection header. Several of these can
also sign in; either route works. Create a key under
**Account, then MCP Keys** at
<https://easy2257.com/profile/account/api-keys>. Keys start with `ez_mcp_`,
are shown once, and are stored as a hash plus the first four characters, which
is how the settings screen tells one key from another. You can hold ten at a
time and revoke any of them at any moment.

Command-line assistants usually take one line:

```
--header "Authorization: Bearer YOUR_KEY"
```

Editors and other assistants usually take a config block:

```json
{
  "mcpServers": {
    "easy2257": {
      "type": "http",
      "url": "https://easy2257.com/api/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_KEY"
      }
    }
  }
}
```

### Run it as a container (clients that cannot set a header)

Some MCP clients can only start a local command over stdio and cannot attach a
header. For those, `agaveis/easy2257-mcp` on Docker Hub is a small image that
bridges stdio to the hosted server. It contains no server code: it runs the
official `mcp-remote` package, pinned by version, and forwards every request to
`https://easy2257.com/api/mcp` with your key as the bearer token. The server is
still hosted by Easy2257; the image only carries the stream.

```
docker run -i --rm -e EASY2257_API_KEY=YOUR_KEY agaveis/easy2257-mcp:latest
```

As a config block:

```json
{
  "mcpServers": {
    "easy2257": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "EASY2257_API_KEY", "agaveis/easy2257-mcp:latest"],
      "env": {
        "EASY2257_API_KEY": "YOUR_KEY"
      }
    }
  }
}
```

The key stays in your environment and is never written into the image or its
logs. Without a key the container exits with a message and does nothing. The
image is built from this repository's [`Dockerfile`](Dockerfile) and
[`bridge/`](bridge/) by the
[`publish-dockerhub`](.github/workflows/publish-dockerhub.yml) workflow, with
the base image, every package and every action pinned.

Every connected assistant, key or sign-in, is listed on the same settings
screen with a one-click disconnect. Revoking ends access immediately.

Included with every Easy2257 plan. The two content log tools are part of the
solo creator plan; on other plans they refuse and say so.

## The sixteen tools

### Productions and scenes

| Tool | What it answers |
|------|-----------------|
| `list_productions` | Your productions with their documentation status and certificate state. |
| `get_production` | One production, scene by scene. |
| `get_scene_compliance` | Per-participant state for one scene: invite state, identity verification, form and document counts, and model release. Participants appear by role and an opaque id, never by name. |
| `list_compliance_gaps` | Every scene with outstanding compliance work, in one call, so an assistant can answer "which scenes still need something?". Cancelled scenes are excluded, and expiring paperwork has its own tool. |
| `list_expiring_documents` | Paperwork that expires within a window you choose, with dates. Anything already overdue is included. |

### Certificates and archives

| Tool | What it answers |
|------|-----------------|
| `get_certificate` | A production's compliance certificates and where each one stands. |
| `verify_certificate` | Whether a certificate someone handed you is current, superseded, or revoked. |
| `get_archive_status` | The sealed archive's hashes for a finalized production. |

### Your account

| Tool | What it answers |
|------|-----------------|
| `get_account_status` | Plan, allowance, and published custodian statement. |
| `get_compliance_requirements` | The document tiers this platform applies, kept separate, plus the participant roles, the checks that produce a gap, and the templates this account can use. |
| `get_removal_requests_summary` | Removal and takedown requests linked to your own records, by status and legal basis. Nothing about who filed one. |
| `list_notifications` | Account notifications. |
| `list_webhook_deliveries` | Webhook delivery outcomes. |

### Solo creators and public codes

| Tool | What it answers |
|------|-----------------|
| `list_content_logs` | A solo creator's own content logs. |
| `get_content_log` | One content log. |
| `verify_record` | The evidence state behind a public record code, which is how a platform confirms what a creator sent it. |

Looking up a code that is not yours is rate limited per credential, the same
whether you signed in or pasted a key, and an exhausted credential learns
nothing, not even whether a code exists. Your own records are free through
`verify_record`. `verify_certificate` always counts, even for your own
certificates; use `get_certificate` for those.

Example questions are in [`docs/example-prompts.md`](docs/example-prompts.md).

## Privacy

[`PRIVACY.md`](PRIVACY.md) covers what this connector transmits and what it
never transmits. The hosted policy is at <https://easy2257.com/privacy>.

## Publishing

`server.json` is the entry in the [official MCP
registry](https://registry.modelcontextprotocol.io) under
`io.github.Agaveis/easy2257-mcp`. It is republished by the
[`publish-registry`](.github/workflows/publish-registry.yml) workflow, which
authenticates with GitHub Actions OIDC, so there is no interactive login and no
stored credential.

## Support

Questions and problems: <https://easy2257.com/contact>.

**Website:** https://easy2257.com
**Listing and source:** https://github.com/Agaveis/easy2257-mcp
Built and maintained by [AgaveIS](https://agaveis.com), Scottsdale, Arizona.
