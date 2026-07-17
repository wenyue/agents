# Project Structure

Strength: `Advisory`

Scope: Generation contract for repository layout, module ownership, dependency direction, shared
locations, and configuration ownership.

## Generation Contract

Author the target rule from observed repository structure and enforced dependency boundaries. Keep
the map selective: record locations and relationships that guide placement or prevent invalid
dependencies, not a directory-by-directory inventory.

## Evidence

- Repository and workspace trees, package manifests, module declarations, and import graphs.
- Feature directories, shared libraries, configuration owners, tests, assets, generated sources,
  scripts, infrastructure, and documentation locations.
- Dependency checks, lint rules, build targets, package boundaries, and representative imports.
- Ownership files and repeated placement patterns that establish stable boundaries.

## Content

- Record top-level areas and the responsibility each one owns.
- Record feature and module layout, placement conventions, and shared locations.
- Record allowed and forbidden dependency directions and the boundaries they protect.
- Record ownership across UI, backend, domain, data, infrastructure, tests, assets, generated
  sources, configuration, scripts, and documentation when those areas exist.
- Record real enforcement mechanisms, but keep their exact invocation in `Project Tools`.

## Boundaries

- Keep tool, runtime, build, test, and verification commands in `Project Tools`.
- Keep API contracts, payloads, domain vocabulary, generated-file edit policy, and lint
  interpretation in `Project Rules`.
- Exclude generic architecture advice, speculative future layout, and directories whose names are
  self-explanatory and impose no placement or dependency constraint.
- Do not duplicate an ownership statement across multiple sections or rules.
