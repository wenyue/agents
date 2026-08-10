# Triage labels

Map the five canonical triage roles used by Matt Skills to the value stored in a local ticket's
`Status:` line:

| Canonical role | Local status | Meaning |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | A maintainer needs to evaluate the ticket. |
| `needs-info` | `needs-info` | The ticket is waiting for more information. |
| `ready-for-agent` | `ready-for-agent` | The ticket is fully specified for an autonomous agent. |
| `ready-for-human` | `ready-for-human` | The ticket requires human implementation. |
| `wontfix` | `wontfix` | The ticket will not be actioned. |

When a Skill says to apply or remove a triage label, update the ticket's single `Status:` value
instead. Operational `claimed` and `resolved` statuses are reserved for wayfinding and ticket
execution; they are not additional triage roles.
