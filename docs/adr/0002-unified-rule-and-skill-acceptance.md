# ADR 0002: Unify the Rule and Skill Acceptance Standard

Status: Accepted

Date: 2026-08-14

## Context

Ordinary Rules, ordinary Skills, and authoring workflows previously used acceptance processes of
different sizes. An initial unification then encoded Candidate Revisions, recovery, and verdicts
as persistent directory trees and ran Review, Acceptance, and fresh re-review sequentially. This
created many empty directories, duplicate candidates, and repeated evidence collection without
leaving reliably recoverable gate state.

The initiating authoring goal is semantic preservation plus clear, concise, executable Rule and
Skill writing. Matt-informed expression and Markdown mechanics support that goal; qualification is
the proof mechanism, not the product objective.

## Decision

SmartKit uses one Acceptance Standard: evidence-driven authoring, independent pruning, machine
validation, fresh Semantic Review, risk-matched Acceptance, and explicit handoff. Different
artifacts use different Acceptance Portfolios, but no portfolio may replace or weaken a gate.

Shared writing and authoring guidance owns expression mechanics. Ordinary authoring and review do
not select or compare external exemplars; they judge the candidate's observable information
hierarchy, executability, and semantic fidelity against accepted evidence. Machine validation must
pass before semantic gates begin. A machine failure stops the run and hands off the exact command,
final exit, relevant output, unrun gates, and unverified surfaces.

One fresh reviewer evaluates one frozen candidate in one bounded task. It performs Semantic Review
first and, only after that passes, runs the candidate's Acceptance Portfolio. The two gates return
separate verdicts. For an Ordinary Artifact, the reviewer judges observable work from an isolated
Acceptance Runner that receives only runtime-visible candidate content, the representative tasks,
and the context or tools needed for those tasks. Every case starts from its frozen input and does
not inherit another case's output. The Runner receives no ledger, expected result,
diff, author reasoning, review finding, or prior case output.

When a proposed instruction exists only to change default Agent behavior and no observed failure
establishes that need, authoring begins with one Behavior Control: the previously accepted artifact
for a rewrite or no candidate for a new artifact. The same case is rerun with the candidate. One
run per case is the default; one confirmation rerun is allowed only for an inconclusive or unstable
result, and divergent results fail rather than permitting a favorable sample to be selected.

Before machine validation, one fresh Pruning Agent that did not author the candidate reads the
complete candidate without its predecessor, diff, author reasoning, intended edits, or expected
verdict. It checks for stale or duplicated meaning, unnecessary caches of environment facts, no-op
instructions, misplaced branch material, and removable wording or structure. It specifically
challenges instructions that only restate an evidenced Agent or host default, repeat a reliably
loaded broader owner, or follow uniquely from the candidate's trigger, inputs, steps, or adjacent
context. Deletion must leave representative actions, choices, authority, safety boundaries, and
exits unchanged; a default requires governing host evidence or an applicable Behavior Control.
The Agent writes no candidate file and cannot later review or run Acceptance for that candidate. A
candidate with only uniquely forced findings gets one author-owned Pruning Pass and one closure
check by the same Agent; a decision-required finding or failed closure stops the run. Passing does
not require a numeric size reduction, but every increase from an available baseline must map to a
distinct supported obligation.

A generation contract is qualified by statically walking its complete guidance against supported
high-risk inputs and starts neither an Acceptance Runner nor target generation. A real target
created later is a separate candidate: it defaults to a different fresh reviewer, inherits neither
evidence nor verdicts, enters the Ordinary Artifact route, and independently passes the normal
Acceptance Standard.

Stop immediately when the first-round findings include `decision-required`; otherwise, one
Correction Pass fixes all `uniquely-forced` findings and returns the corrected revision through the
Pruning Gate and invalidated machine checks. A different fresh Closure Reviewer gets one closure
attempt: confirm that the findings are closed, recheck changed obligations and exits, falsify the
complete artifact, and rerun affected Acceptance cases. Stop after another failure; a user decision
does not automatically reset the correction or review budget for the same run.

A Qualification Campaign applies the same standard to multiple representative Canary Candidates;
it does not define another quality tier. Candidates are corrected and frozen independently in the
active checkout or a necessary Task Worktree and are invalidated according to their dependencies;
only the Adoption Gate accepts them together as the repository result. When changing the Acceptance
Standard itself, evaluate the candidate against the previously accepted Standard and the current
accepted Spec so the candidate cannot qualify by weakening its own grader.

A Candidate Revision is a logical content state in the active checkout or a necessary Task
Worktree, not a copied directory tree. Qualification creates no persistent workspace or report;
the Review Packet is assembled on demand, and the final handoff records commands, exits, verdicts,
and unverified surfaces. Reusable evaluation cases are versioned test inputs, not retained run
state. Generated candidates, mutable working copies, Git state, verdicts, and Acceptance sandboxes
remain temporary.

The reusable authoring Skill has one shared workflow and four disclosed references. The main file
owns routing, readiness, evidence, candidate state, validation, review, correction, and handoff.
`ordinary-artifact.md` and `generation-contract.md` own the two lifecycle branches; `rule.md` and
`skill.md` own the two semantic types. Each route loads one reference from each pair. An ordinary
artifact selects its own semantic type; a generation contract is an instruction artifact and
selects the type of its future target. Authoring and Acceptance requirements for one concern remain
co-located in that concern's reference.

A shared artifact needs evidence that its policy or job is independent of project-local facts. One
representative traceable context plus direct portability evidence is the default; a second context
is required only when portability materially affects acceptance and direct evidence cannot resolve
it. A Project-local artifact may use a small self-contained project when repository Rules,
configuration, files, or commands affect its behavior.

## Consequences

Ordinary authoring and workflow qualification share the same quality language and termination
conditions. One bounded Pruning Gate separates editorial reduction from semantic falsification;
one bounded Candidate Review avoids duplicate reviewer context loading; an isolated Acceptance
Runner demonstrates use without receiving the answer. Risk-matched cases, conditional Behavior
Control, one Pruning Pass, one Correction Pass, and one Closure Review bound the added cost and
prevent a serial fix loop. The project task contract owns a Qualification Campaign's specific
canaries, scheduling, budget, Defect Cards, and write scope; they do not enter the cross-project
`write-rules-and-skills` runtime Skill. Project Rules and tests own the location, integrity, and
runtime isolation of committed evaluation inputs.
