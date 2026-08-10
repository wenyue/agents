# 02 — Unified ownership engine

Category: enhancement
Status: resolved
Blocked by: 01

## What to build

Introduce `.agents/smartkit.lock.json` and one generic ownership model for files, directory trees,
and structured fields.

- [x] Every managed asset has a deterministic semantic digest and descriptive role.
- [x] First adoption accepts only missing or equal assets.
- [x] Later runs verify every previous digest before planning any write.
- [x] Removed assets come only from the previous/current manifest difference.
- [x] Seeded project documents remain visible without granting update or deletion authority.
- [x] External source commit and detected license metadata are recorded without secret values.

## Comments

- The reconciler is independent of Rule, Skill, Agent, wrapper, and MCP naming conventions.
