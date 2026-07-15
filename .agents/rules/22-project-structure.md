# Project Structure

Strength: `Advisory`

Scope: Generation contract for repository layout, module ownership, dependency direction, shared
locations, and configuration ownership.

## Generation Contract

Author the target rule from observed repository structure and enforced dependency boundaries. Keep
the map selective: include locations and relationships that guide placement or prevent invalid
dependencies, not a directory-by-directory inventory.

## Evidence

- Repository and workspace trees, package manifests, module declarations, and import graphs.
- Feature directories, shared libraries, configuration owners, tests, assets, generated sources,
  scripts, infrastructure, and documentation locations.
- Dependency checks, lint rules, build targets, package boundaries, and representative imports.
- Ownership files or repeated placement patterns that establish a stable boundary.

## Content

- Record top-level areas and the responsibility each one owns.
- Record feature or module layout, placement conventions, and shared locations.
- Record allowed and forbidden dependency directions and the boundary they protect.
- Record ownership boundaries across UI, backend, domain, data, infrastructure, tests, assets,
  generated sources, configuration, scripts, and documentation when those areas exist.
- Name real enforcement mechanisms, but leave their exact invocation in `20-project-tools.md`.

## Boundaries

- Keep tool, runtime, build, test, and verification commands in `20-project-tools.md`.
- Keep API contracts, payloads, domain vocabulary, generated-file edit policy, and lint
  interpretation in `21-project-rules.md`.
- Exclude generic architecture advice, speculative future layout, and directories whose names are
  self-explanatory and impose no placement or dependency constraint.
- Do not duplicate the same ownership statement across multiple sections or rules.
