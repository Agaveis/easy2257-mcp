# easy2257-mcp: the Easy2257 MCP connector

This repository is the public listing for the Easy2257 [Model Context
Protocol](https://modelcontextprotocol.io) server. The server itself is hosted
by Easy2257 and reached over the network, so there is nothing here to install
and no engine source: this repo holds the registry metadata, the privacy
statement, and the setup notes.

**Endpoint:** `https://easy2257.com/api/mcp` (Streamable HTTP)
**Setup and screenshots:** <https://easy2257.com/ai-assistant>

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

What comes back is compliance state: ids, public codes (`SCENE-`, `PROJ-`,
`LOG-`), statuses, counts, dates, and content hashes. It never returns
performer names, dates of birth, ID numbers, images, file paths, addresses, or
the contents of anyone's documents. That is a deliberate boundary, not a gap,
and it is what makes this surface safe to point a shared assistant at: there is
no identity data in it to leak.

Three guarantees, restated plainly:

- **It only reads.** No tool creates, changes, signs, or deletes a record.
- **No identity data crosses the wire.** Statuses, codes, counts, dates, and
  integrity hashes only.
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
and anything else that lets you set a connection header. Create a key under
**Account, then MCP Keys** at
<https://easy2257.com/profile/account/api-keys>. Keys start with `ez_mcp_`,
are shown once, and are stored only as a hash. You can hold ten at a time and
revoke any of them at any moment.

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

Every connected assistant, key or sign-in, is listed on the same settings
screen with a one-click disconnect. Revoking ends access immediately.

Included with every Easy2257 plan.

## The sixteen tools

### Productions and scenes

| Tool | What it answers |
|------|-----------------|
| `list_productions` | Your productions with their documentation status and certificate state. |
| `get_production` | One production, scene by scene. |
| `get_scene_compliance` | Exactly what is outstanding on a scene: pending invites, unverified identities, unsigned forms, missing releases. |
| `list_compliance_gaps` | Everything outstanding across the account, so an assistant can answer "what still needs work?" in one call. |
| `list_expiring_documents` | Paperwork coming up for renewal, with dates. |

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
| `get_compliance_requirements` | The document requirements a complete record has to meet. |
| `get_removal_requests_summary` | Removal and takedown requests linked to your own records, by status and legal basis. Nothing about who filed one. |
| `list_notifications` | Account notifications. |
| `list_webhook_deliveries` | Webhook delivery outcomes. |

### Solo creators and public codes

| Tool | What it answers |
|------|-----------------|
| `list_content_logs` | A solo creator's own content logs. |
| `get_content_log` | One content log. |
| `verify_record` | The evidence state behind a public record code, which is how a platform confirms what a creator sent it. |

Lookups of codes that are not yours are rate limited per key, and an exhausted
key learns nothing, not even whether a code exists.

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
