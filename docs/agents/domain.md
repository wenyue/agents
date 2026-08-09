# Domain docs

This repository uses a single-context domain documentation layout.

## Before exploring

- Read the root `CONTEXT.md` when it exists.
- Read applicable ADRs under `docs/adr/` when that directory exists.
- Proceed silently when either source is absent; domain-modeling creates them when the project
  resolves terminology or architectural decisions that need a durable record.

Use glossary terms exactly as `CONTEXT.md` defines them. When a specification or implementation
would contradict an ADR, surface that conflict explicitly instead of silently overriding it.
