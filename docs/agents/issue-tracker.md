# Issue tracker: Local Markdown

Issues and specs for this repository live as Markdown files under `.scratch/`. Do not create,
read, update, label, comment on, or close GitHub issues for repository work.

## Conventions

- Keep one effort per `.scratch/<effort-slug>/` directory.
- Store its specification at `.scratch/<effort-slug>/spec.md`.
- Store each implementation ticket at
  `.scratch/<effort-slug>/issues/<NN>-<ticket-slug>.md`, numbered from `01` in dependency order.
- Record `bug` or `enhancement` in a `Category:` line when a ticket needs triage classification.
- Record exactly one canonical triage state in a `Status:` line; use the mapping in
  `docs/agents/triage-labels.md`.
- Append discussion and triage history under a `## Comments` heading in the same file.

## Operations

- Publish a specification by writing `.scratch/<effort-slug>/spec.md` with
  `Status: ready-for-agent` near the top.
- Publish tickets as separate files under `.scratch/<effort-slug>/issues/`; do not combine them into
  one ticket file.
- Fetch a referenced specification or ticket by reading its repository-relative path. When the
  user supplies only a ticket number, resolve it within the current effort directory.
- List work by scanning `.scratch/*/issues/` and filtering the `Status:` and `Category:` fields.
- Apply a triage outcome by replacing the ticket's `Status:` value and appending any required note
  under `## Comments`.
- Close rejected work by setting `Status: wontfix` and recording the reason under `## Comments`;
  preserve the file as the decision record.

## Ticket Format

Use this metadata near the top of every ticket:

```markdown
Category: enhancement
Status: ready-for-agent
Blocked by: None
```

`Blocked by:` lists the numbers of unfinished prerequisite tickets. A ticket is on the frontier
when its status is `ready-for-agent` and every listed blocker is `resolved`.

## Wayfinding Operations

For `/wayfinder`, store the map at `.scratch/<effort-slug>/map.md` and each child decision at
`.scratch/<effort-slug>/issues/<NN>-<slug>.md`.

- Record `Type: research|prototype|grilling|task` on each child.
- Claim a frontier child by changing its status from `ready-for-agent` to `claimed` before work.
- Resolve it by appending the answer under `## Answer`, changing its status to `resolved`, and
  adding a context pointer to the map's decisions-so-far.
