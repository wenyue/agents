# Issue tracker: GitHub

Issues and specs for this repository live as GitHub issues in `wenyue/agents`. Use the `gh` CLI
from this checkout so it resolves the repository from `origin`.

## Operations

- Create: `gh issue create --title "..." --body-file <path>`.
- Read: `gh issue view <number> --comments`.
- List: `gh issue list` with the labels and state required by the workflow.
- Comment: `gh issue comment <number> --body-file <path>`.
- Label: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Close: `gh issue close <number> --comment "..."`.

When a Skill says to publish to the issue tracker, create a GitHub issue. Pull requests are not a
request or triage surface for this repository.
