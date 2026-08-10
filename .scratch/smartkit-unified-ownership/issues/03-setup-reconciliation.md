# 03 — Setup reconciliation through one manifest

Category: enhancement
Status: resolved
Blocked by: 02

## What to build

Route the public setup workflow through the unified ownership engine and delete resource-specific
project lock and catalog-history behavior.

- [x] Rules, Skills, Agents, wrappers, config fields, and MCP fields share one manifest.
- [x] User-owned sibling fields, Rules, Skills, and seeded documents are preserved.
- [x] Modified owned assets and conflicting first-adoption targets fail before writes.
- [x] Catalog retirement lists and both project-specific lock readers/writers are removed.
- [x] Ownership content and manifest updates use the existing transactional plan/application path.
- [x] Workflow tests cover adoption, removal, preservation, conflicts, and no-op convergence.

## Comments

- Historical paths and field names are not retained in the implementation.
