# SmartKit

SmartKit distributes reusable agent capabilities while preserving each target repository's
ownership of its project-specific agent configuration.

## Language

**Harness**:
An agent host application, such as Codex, Cursor, or GitHub Copilot, that loads and executes
SmartKit capabilities through its native interfaces.
_Avoid_: Platform, operating system, runtime

**Platform**:
An operating-system family, such as Windows, Linux, or macOS, on which a Harness and SmartKit run.
_Avoid_: Harness, agent host

**Harness Adaptation**:
A plugin-private, Harness-scoped Rule that maps shared SmartKit actions to one Harness's native
tools, capabilities, lifecycle semantics, constraints, and missing-capability fallbacks.
_Avoid_: Platform adaptation, duplicated workflow policy

**Skill Governance**:
The shared policy that constrains Skill authority, precedence, and routing regardless of whether a
Skill is project-owned, plugin-owned, or external.
_Avoid_: Skill configuration, plugin governance, Agent orchestration

**Workspace Policy**:
The shared policy that selects the current workspace or a Task Worktree and governs local Git state,
commit authority, and remote actions independently of any Skill workflow.
_Avoid_: Skill configuration, worktree Skill, repository setup

**Plugin MCP**:
An MCP server distributed with the SmartKit plugin and made available through each supported
host's plugin integration.
_Avoid_: Global MCP, shared project MCP

**Project MCP**:
An MCP server declared by a target repository as canonical project configuration and rendered by
setup into the native configuration of each enabled host.
_Avoid_: Plugin MCP, hard-coded project template

**MCP Adapter**:
A host-native MCP configuration generated from a canonical Plugin MCP or Project MCP declaration.
_Avoid_: MCP source, handwritten harness copy

**Managed Asset**:
A project file, directory tree, or structured field that setup may update or delete because its
identity and current digest are recorded in the SmartKit Ownership Manifest.
_Avoid_: User-owned asset, inferred-by-name asset

**SmartKit Ownership Manifest**:
A target repository record of resolved external sources, digest-bearing managed assets, and
non-owned seeded documents.
_Avoid_: External Skill lock, Project MCP lock, migration ledger

**Configured MCP**:
An MCP capability delivered as host configuration while its server remains owned by an external
package, remote service, or project runtime; SmartKit does not copy the server implementation merely
to distribute the configuration.
_Avoid_: Vendored MCP, installed MCP

**Vendored Plugin Skill**:
A third-party Skill reviewed, licensed, locked, and copied into SmartKit before release because the
supported plugin hosts load Skills from plugin-local paths and do not share a remote Skill dependency
contract.
_Avoid_: Referenced Skill, runtime-fetched Skill

**Static MCP Readiness**:
The configuration and local prerequisites that can be checked without starting an MCP server,
probing a remote endpoint, triggering authentication, or requiring an application runtime to be live.
_Avoid_: MCP health, live MCP availability

**Daily Project Check Gate**:
The first step of the automatic check pipeline, allowing at most one evaluation per canonical project
root, Harness, and local calendar day regardless of the number or outcome of downstream checks.
_Avoid_: Global daily check, per-check throttle, session throttle

**MCP Readiness Profile**:
A typed, non-interactive static check set interpreted after the Daily Project Check Gate. Plugin MCP
declares it explicitly; Project MCP derives it from command paths and environment-variable names.
_Avoid_: MCP-specific Hook, arbitrary check script

### Authoring Evaluation

**Ordinary Artifact**:
A Rule or Skill used directly as policy or as a triggered job rather than as instructions for
authoring another Rule or Skill.
_Avoid_: Runtime artifact, generated target

**Generation Contract**:
A standalone instruction artifact that guides another Agent in authoring a complete future Rule or
Skill. The future target determines whether Rule or Skill semantics apply; the contract itself uses
static walkthrough, while a real target is reviewed later as an Ordinary Artifact.
_Avoid_: Generated target, generator fixture

**Qualification Campaign**:
One bounded application of the Acceptance Standard across the representative canary classes needed
to qualify the SmartKit authoring workflow.
_Avoid_: Separate acceptance standard, full rewrite, canary cycle

**Acceptance Standard**:
The single quality contract every authored Rule, Skill, or Generation Contract must satisfy through
evidence-backed authoring, machine validation, fresh semantic review, risk-matched acceptance, and
explicit handoff.
_Avoid_: Qualification-only gate, ordinary acceptance

**Acceptance Portfolio**:
The artifact-specific cases, evidence contexts, executable checks, static walkthroughs, and
regression defects used to demonstrate that one candidate satisfies the Acceptance Standard.
_Avoid_: Acceptance level, alternate standard

**Canary Candidate**:
One independently evaluated version of a representative Ordinary Artifact or Generation Contract
in a Qualification Campaign.
_Avoid_: Candidate bundle, whole-campaign version

**Candidate Revision**:
The complete current content state of one authored candidate. Validation, Review, and Acceptance
evidence applies only while that state is unchanged; it does not require a copied tree.
_Avoid_: Revision directory, inherited verdict

**Owner Gate**:
The pre-authoring decision point that classifies each obligation and its complete artifact as Rule,
Skill, Split, Environment-owned, or Ambiguous, then compares that verdict with the requested or
current owner.
_Avoid_: Approval gate, Rule approval

**Ownership Review**:
The read-only `write-rules-and-skills` branch that applies the Owner Gate to existing artifacts and
exits with supported ownership verdicts without creating a Candidate Revision.
_Avoid_: Separate Skill, Candidate Review

**Policy Frame**:
The semantic structure of one Rule, relating its owner and strength, scope and applicability,
observable predicate-to-outcome mappings, exceptions, precedence, and ownership boundaries without
describing a triggered job procedure.
_Avoid_: Rule workflow, policy rationale

**Generation Frame**:
The semantic structure of one Generation Contract, relating its future target and owner, required
evidence and obligations, permitted writes, validation, handoff, and material-ambiguity stops while
leaving unsupported authoring method and order to Agent judgment.
_Avoid_: Generated target outline, mandatory authoring recipe

**Skill Shape**:
The authoring posture selected for one Skill from supported evidence: Judgment-led,
Procedure-led, or Hybrid.
_Avoid_: Skill type, document format

**Judgment-led Skill**:
A Skill that constrains its objective, evidence, principles, invariants, decision boundaries, and
exits while leaving the method to Agent judgment.
_Avoid_: Descriptive Skill, unstructured Skill

**Procedure-led Skill**:
A Skill that prescribes supported actions or ordering because the process materially affects
correctness, safety, external protocol compliance, coordination, recovery, or the accepted outcome.
_Avoid_: Detailed Skill, complete workflow

**Hybrid Skill**:
A Judgment-led Skill containing one or more evidence-backed Procedural Islands while leaving the
remaining method to Agent judgment.
_Avoid_: Partially specified Skill, mixed document

**Judgment Frame**:
The semantic structure of a Judgment-led Skill, relating its objective, evidence, principles,
invariants, decision boundaries, and prioritized exits without prescribing an unsupported method.
_Avoid_: Job Graph, procedure outline

**Job Graph**:
The semantic structure of a Procedure-led Skill or Procedural Island, relating its entry, actions,
branches, runtime resources, and prioritized exits independently of any document outline.
_Avoid_: Markdown outline, procedure draft

**Execution Path**:
One reachable route through a Job Graph from its entry to exactly one prioritized completion, stop,
or failure exit.
_Avoid_: Phase list, branch inventory

**Procedural Island**:
One bounded Procedure-led part of a Hybrid Skill that returns control to Agent judgment after its
prioritized exit.
_Avoid_: Workflow phase, procedural Skill

**Artifact Projection**:
The placement of each Judgment Frame, Job Graph, or Procedural Island obligation into its narrowest
reliable runtime owner and loading tier without changing the Skill's observable behavior.
_Avoid_: Content splitting, editorial reorganization

**Entry Sufficiency**:
The property that a Skill's main file identifies its Skill Shape, objective or entry, applicable
Judgment Frame or Execution Path, and conditionally required resources without unrelated detail.
_Avoid_: Self-contained main file, short main file

**Path Sufficiency**:
The property that a Skill's main file plus the resources selected by one Execution Path are enough
to execute that path to its unique prioritized exit.
_Avoid_: Whole-Skill self-containment, eager resource loading

**Frozen Canary**:
A Canary Candidate whose own machine validation, semantic review, and representative acceptance
have passed and whose evidence has not been invalidated.
_Avoid_: Approved campaign, immutable file

**Adoption Gate**:
The all-or-none boundary that permits repository adoption only after every required Canary Candidate
has passed its own gates.
_Avoid_: Campaign restart, per-canary writeback

**Correction Loop**:
The authoring cycle that applies all current uniquely forced findings, reruns invalidated gates, and
continues while each revision makes progress toward a passing Candidate Revision.
_Avoid_: User-confirmed retry, fixed correction budget, one-finding patch

**Fresh Reviewer**:
An Agent that did not author the Candidate Revision it evaluates. A generation contract and a real
target created later default to different Fresh Reviewers, receive separate reviews, and do not
inherit verdicts.
_Avoid_: Author self-review, inherited reviewer

**Acceptance Runner**:
An isolated fresh Agent that applies one Ordinary Artifact to one representative task using only
the candidate's runtime-visible content, the task, and its required context or tools. The Runner
does not receive the semantic ledger, expected result, diff, author reasoning, review findings, or
prior case output; the Fresh Reviewer judges its observable result.
_Avoid_: Acceptance reviewer, prepared-answer agent, paper walkthrough

**Behavior Control**:
One isolated run before authoring that uses the previously accepted artifact for a rewrite or no
candidate for a new artifact. Use it only when a proposed instruction's sole supported purpose is
to change default Agent behavior and no observed failure already establishes that need.
_Avoid_: Mandatory baseline, repeated sampling, generation target

**Candidate Review**:
One bounded task in which a Fresh Reviewer performs Semantic Review first, then judges the
candidate's Acceptance Portfolio from isolated Acceptance Runner results or the Generation
Contract's static walkthrough, and returns a separate verdict for each gate.
_Avoid_: Review Board, combined verdict

**Regression Corpus**:
The maintained set of minimal, previously demonstrated authoring defects replayed in later
Qualification Campaigns.
_Avoid_: Exhaustive scenario matrix, ad hoc mutants

**Review Packet**:
The bounded evidence shared with the Fresh Reviewer for one candidate, excluding author reasoning,
suspected defects, intended fixes, and expected verdicts.
_Avoid_: Repository snapshot, author handoff

**Defect Card**:
One minimal Regression Corpus case containing a supported input, one injected semantic defect, and
the review gate it should violate.
_Avoid_: Full broken candidate, string assertion

### Worktree Lifecycle

**Ticket Batch**:
A frozen dependency-ordered set of implementation tickets whose per-ticket Task Commits are
accumulated, reviewed, and delivered as one scope.
_Avoid_: Ticket queue, combined task, batch commit

**Batch Worktree**:
A named isolated linked worktree whose branch accumulates the ordered Task Commits for one Ticket
Batch while the delivery target remains unchanged.
_Avoid_: Ticket worktree, base checkout, shared worktree

**Task Worktree**:
A named, isolated linked worktree whose branch and local state belong exclusively to one accepted
implementation task.
_Avoid_: Worktree, base checkout, shared worktree

**Checkpoint Commit**:
A provisional commit that preserves a recoverable implementation state within a Task Worktree and
is not part of the promised final history.
_Avoid_: Final commit, Task Commit

**Task Commit**:
A single delivery-history commit that consolidates one accepted task's Checkpoint Commits. In a
Ticket Batch it remains staged until the whole batch passes review and verification.
_Avoid_: Checkpoint Commit, squash commit

**Batch Review Commit**:
The optional final Task Commit that consolidates fixes produced by the whole-batch review without
rewriting the preceding per-ticket Task Commits.
_Avoid_: Ticket Task Commit, amended ticket commit, review checkpoint

**Staged Ticket**:
A Ticket whose Task Commit has been appended to its Batch Worktree but whose batch has not yet been
delivered to the final target. It remains claimed and is not completed.
_Avoid_: Delivered Ticket, completed Ticket, merged Ticket

**Batch Delivery**:
The verified fast-forward of a reviewed Ticket Batch's ordered Task Commit range and optional Batch
Review Commit to its unchanged final target.
_Avoid_: Ticket staging, tracker completion, batch merge

**Ticket Completion**:
The tracker transition performed by the Ticket Batch controller after Batch Delivery is proven.
_Avoid_: Ticket staging, Task Commit creation, Git cleanup

**Finalization Contract**:
The closed, mode-discriminated interface by which a caller supplies Git identities, evidence,
history, target, recovery, cleanup, and authorization policy to `finish-worktree`.
_Avoid_: Tracker contract, generic parameter bag, Ticket Batch orchestration

**Already Delivered**:
A terminal state in which the selected target is proven to contain the complete accepted task
result, so no Task Commit or delivery mutation is needed.
_Avoid_: Empty Task Commit, no diff
