# Privacy: the Easy2257 MCP connector

The hosted policy that governs the Easy2257 service is at
<https://easy2257.com/privacy>. This document covers the one thing that policy
cannot: exactly what an AI assistant sees when you connect it.

## What the connector transmits

Compliance state about your own account, and only that:

- Record identifiers and public codes (`SCENE-`, `PROJ-`, `LOG-`).
- Statuses: whether an identity is verified, whether a form is signed, whether
  a scene is complete, whether a certificate is current, superseded, or
  revoked.
- Counts, dates, and deadlines.
- Content and archive integrity hashes.
- Short labels you wrote yourself, such as a production or scene title, echoed
  back only to the account that owns them.

## What the connector never transmits

Not redacted, not truncated. Never selected in the first place:

- Performer names, dates of birth, or ID numbers.
- Images, scanned documents, or the contents of any document.
- File paths, storage keys, or download links to stored evidence.
- Addresses, contact details, or IP addresses.
- Anything about a person who filed a removal request.
- Any other producer's records.

Every query behind a tool is a named, fixed selection of columns. A test suite
runs all sixteen tools against deliberately poisoned rows and fails the build
if any identifying key or value reaches the output.

## What the connector cannot do

It is read-only. No tool creates, changes, signs, or deletes a record. No tool
attests to anything on your behalf. No tool touches checkout, scene activation,
or any paid action. Attestations and payments happen at easy2257.com, made by a
person, on purpose.

## Credentials

Two ways to connect, one authorization story.

- **Pasted key.** Keys begin with `ez_mcp_`, are shown once, and are stored
  only as a hash. Up to ten active keys per account. Revoking one ends its
  access immediately. All keys are revoked on a password reset.
- **Sign-in.** OAuth 2.1 with PKCE, one scope (`mcp:read`), access tokens valid
  for one hour and refresh tokens for thirty idle days with rotation. The
  assistant never receives your password.

Either way, the credential resolves to your account and only your account.

## Scope limiting on lookups

Looking up a public record code that does not belong to you is rate limited per
credential. A miss counts against the limit, so an exhausted credential learns
nothing, not even whether a code exists. Lookups of your own records are not
limited.

## Where the data goes

The connector answers your assistant's tool calls. Whatever your assistant does
with the answers, including sending them to the model provider that runs it, is
governed by that assistant's own privacy policy, not this one.

## Contact

<https://easy2257.com/contact>
