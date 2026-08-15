# SmartKit Rule and Skill Authoring and Qualification

Status: ready-for-agent

## Problem Statement

SmartKit needs a reliable way to create and update Rules and Agent Skills without requiring the
user to invoke a separate grilling workflow first. The original goal is to preserve the complete
behavior of existing first-party artifacts while learning the strongest expression and Markdown
information-design patterns visible in Matt Skills. The resulting documents should be concise,
easy to scan, and easy for another Agent to execute without turning Matt's domain-specific behavior
into SmartKit policy. The authoring Agent must understand the current behavior, owner boundaries,
preserved semantics, project constraints, and validation seams before writing.

Later attempts improved semantic completeness but made validation too slow: reviews were
serialized, each correction caused another complete reread, qualification copied whole revision
trees, generated empty directories, and stored records that still did not reliably resume the
gates. Those failures constrain the solution, but they are not the reason the authoring Skill is
being redesigned.

The authoring contract also risked mixing project facts into a cross-project Skill, expanding
runtime documents with review metadata, and using brittle Markdown or translation assertions as a
substitute for semantic review. The result must preserve every supported behavior while producing
concise Matt-like documents whose Markdown structure carries meaning. It must prove that ordinary
Rules, ordinary Skills, scripted Skills, and generation contracts meet the same quality standard
without exhaustive natural-language oracles, persistent qualification workspaces, or unbounded
review loops.

## Solution

Provide one cross-project SmartKit entry point that routes each request along two dimensions: an
ordinary artifact or a generation contract, and the semantic type of the ordinary artifact or
future target. A generation contract is an instruction artifact rather than an ordinary Rule or
Skill; its target type selects `rule.md` or `skill.md`. The main `SKILL.md` owns the shared
readiness, evidence, semantic-ledger, candidate, validation, review, correction, and handoff
workflow. Four disclosed references own the non-overlapping specialized requirements:

- `ordinary-artifact.md` covers directly used Shared and Project-local artifacts plus their
  representative application;
- `generation-contract.md` covers instructions that author future targets plus their static
  walkthrough;
- `rule.md` covers Rule semantics and Rule-specific cases; and
- `skill.md` covers Skill semantics and Skill-specific cases.

Each route loads one lifecycle reference and one semantic-type reference. Authoring and Acceptance
requirements for one concern stay together in its owning reference. Project Rules and owner
contracts supply project-specific facts; the reusable Skill supplies only SmartKit authoring
mechanics.

Use the Matt-informed `writing-for-agents` mechanics to carry transferable expression techniques:
visible action order, steps-versus-reference separation, progressive disclosure, co-location,
leading words, checkable completion criteria, positive instructions, pruning, and meaningful
Markdown. Ordinary authoring does not select or compare Matt exemplars. Apply a technique only when
it lowers context or cognitive load without weakening a preserved obligation. Align Rule and Skill
authoring language and information architecture wherever the underlying concepts are genuinely
parallel.

Every authored candidate uses one Acceptance Standard: focused machine validation, a frozen
Candidate Revision, one fresh reviewer who performs Semantic Review before the candidate's
risk-matched Acceptance and returns separate verdicts, at most one evidence-forced Correction Pass,
one different fresh Closure Reviewer, and an explicit handoff. Ordinary Artifact Acceptance uses
an isolated fresh Runner that receives runtime-visible inputs rather than the reviewer-only answer.
Generation Contract Acceptance remains a static walkthrough and starts neither a Runner nor target
generation. Reviewer roles are scoped to one candidate: a generation contract and a real target
created later are separate candidates, default to different fresh reviewers, receive separate
verdicts, and do not inherit one another's evidence.

Qualification uses the same standard with a risk-matched Acceptance Portfolio. Candidate state
lives in the active checkout or one necessary Task Worktree. It creates no persistent
qualification workspace, revision tree, or report. Six independent version-controlled cases live
under `tests/fixtures/write-rules-and-skills/`; Project-local cases may include a small project, but
generated candidates, verdicts, and mutable run state remain temporary. Generation-contract cases
review the guidance statically and do not generate a fake target. A target created later in a real
project enters the ordinary-artifact route before adoption.

## User Stories

1. As a maintainer, I want an Agent to understand the accepted outcome before writing, so that implementation does not begin from a guessed interpretation.
2. As a maintainer, I want the Agent to inspect current behavior, owners, dependencies, and validation seams, so that a rewrite remains connected to the real system.
3. As a maintainer, I want the Agent to ask only when evidence still permits materially different results, so that routine authoring is autonomous without inventing intent.
4. As an authoring Agent, I want stable implementation, configuration, and tests to resolve environmental facts, so that missing prose does not create unnecessary blockers.
5. As a maintainer, I want every supported semantic obligation preserved, so that rewriting does not silently change behavior.
6. As an authoring Agent, I want one independently changeable obligation per semantic-ledger row, so that omissions and unsupported changes are reviewable.
7. As an authoring Agent, I want every ledger row to have one owner and disposition before writing, so that policy and procedure do not drift between artifacts.
8. As a reviewer, I want every changed or retired obligation backed by current evidence or explicit approval, so that cleanup cannot remove live behavior.
9. As a reviewer, I want unsupported thresholds, predicates, commands, recoveries, and exits rejected, so that precision is never invented to make a document look complete.
10. As an authoring Agent, I want persistent policy routed to a Rule, so that policy remains continuously applicable without an invented workflow.
11. As an authoring Agent, I want a trigger-started job routed to a Skill, so that its actions and observable exits are executable.
12. As a maintainer, I want mixed policy and procedure split into separately owned Rule and Skill artifacts, so that each has one meaning and one owner.
13. As a Rule author, I want class, owner, strength, scope, applicability, precedence, exceptions, boundaries, and outcomes resolved, so that the policy yields one result for supported facts.
14. As a Rule reviewer, I want nearest included and excluded cases exercised, so that hidden false positives and false negatives are exposed.
15. As a Rule reviewer, I want overlapping Rules and exceptions to have deterministic outcomes, so that delivery order never becomes an implicit conflict resolver.
16. As a Skill author, I want actor, trigger, inputs, preconditions, start, actions, outcome, owner, boundaries, validation, resources, and handoff resolved, so that another Agent can execute the job without invention.
17. As a Skill reviewer, I want completion, stop, failure, and recovery exits complete and prioritized, so that coincident conditions never produce two actions or no action.
18. As a Skill author, I want scripts only for work that is simultaneously repeated, fragile, and deterministic, so that simple prose is not replaced by unnecessary machinery.
19. As a Skill author, I want every owned script's dependencies, inputs, outputs, failures, recovery, and safe tests defined, so that executable work has a complete contract.
20. As a runtime Agent, I want resources referenced only when the job consumes them, so that Skill packages stay small and navigable.
21. As a generation-contract author, I want complete target packaging, policy or job, schema, owner split, and write target defined, so that generation cannot stop at a placeholder.
22. As a generated-target user, I want the target to contain its complete runtime semantics, so that it does not depend on an authoring pointer.
23. As a generation-contract author, I want generation to stop when target evidence permits materially different outputs, so that target facts are never guessed.
24. As a cross-project Skill user, I want reusable SmartKit mechanics separated from project facts, so that the Skill works in any SmartKit-based repository.
25. As a project maintainer, I want language, mirror, source-authority, distribution, command, and host facts owned by project Rules or configuration, so that the reusable Skill does not encode one repository.
26. As a project Agent, I want to load applicable local authorities at runtime, so that cross-project authoring respects the current repository.
27. As a runtime Agent, I want final Rules and Skills to contain only schema-required or behavior-changing instructions, so that review evidence and provenance do not bloat runtime context.
28. As a maintainer, I want Matt-like information hierarchy and meaningful Markdown, so that concise documents remain easy for Agents and humans to navigate.
29. As a reviewer, I want Markdown forms used only when they change interpretation or execution, so that formatting does not become decorative structure.
30. As a test author, I want machine validation limited to structured or executable facts, so that passing tests do not falsely claim natural-language correctness.
31. As a test author, I want ordinary sentences, translated wording, physical wrapping, and complete heading lists excluded from snapshots, so that harmless prose changes do not break tests.
32. As an authoring Agent, I want focused checks run before semantic review, so that deterministic defects are rejected cheaply.
33. As a maintainer, I want complete repository verification run once at Adoption, so that candidate work does not repeatedly pay the full-suite cost.
34. As a reviewer, I want line, word, and byte changes compared with the baseline, so that unsupported document growth is visible without a rigid size threshold.
35. As a reviewer, I want a Candidate Revision to mean one complete current content state, so that evidence validity is clear without copied revision directories.
36. As a maintainer, I want candidate state represented by the active checkout or one necessary Task Worktree, so that Git remains the change owner.
37. As a maintainer, I want no persistent qualification workspace or report by default, so that validation does not create duplicate state.
38. As a maintainer, I want generated candidates, mutable project copies, Git state, and Acceptance sandboxes kept out of committed fixtures, so that qualification leaves no stale working state.
39. As a reviewer, I want candidate writes frozen during Candidate Review, so that both verdicts apply to the same content.
40. As a reviewer, I want Review and Acceptance evidence discarded if the frozen candidate changes, so that stale verdicts cannot be reused.
41. As a maintainer, I want one fresh reviewer to perform Semantic Review first and then the candidate's Acceptance in one bounded task, so that independence does not require duplicate context loading.
42. As a maintainer, I want Semantic Review and Acceptance to produce separate verdicts, so that semantic completeness and representative behavior remain distinct gates.
43. As a reviewer, I want a bounded Review Packet without author reasoning, suspected defects, intended fixes, or expected verdicts, so that review remains independent.
44. As a reviewer, I want two to four high-risk supported counterexamples rather than exhaustive prose matrices, so that review remains adversarial and bounded.
45. As a Rule user, I want Representative Acceptance to cover applicable, excluded, boundary, and conflict cases, so that policy behavior is demonstrated.
46. As a Skill user, I want Representative Acceptance to cover the main path and highest-risk non-completion paths, so that the job's exits are demonstrated.
47. As a maintainer, I want real public entry points used where available, so that Acceptance exercises observable behavior instead of an author-written oracle.
48. As a maintainer, I want unavailable execution reported as untested rather than machine-passed, so that walkthrough evidence is not overstated.
49. As an authoring Agent, I want findings from both candidate gates aggregated before correction, so that one pass can address the whole defect set.
50. As a maintainer, I want any decision-required finding to stop automatic correction, so that the Agent cannot choose new policy or authority.
51. As a maintainer, I want all uniquely forced findings corrected in one Correction Pass, so that review cannot degrade into one-finding patches.
52. As a maintainer, I want a different fresh Closure Reviewer after correction, so that the author and first reviewers do not certify their own fixes.
53. As a Closure Reviewer, I want every finding, affected obligation, exit, and Acceptance case rechecked, so that closure proves more than textual replacement.
54. As a maintainer, I want Closure failure to stop the run, so that validation cannot enter a third automatic correction loop.
55. As a maintainer, I want a user decision not to reset the same run's automatic review budget, so that repeated authorization cannot create an unbounded cycle.
56. As a maintainer, I want a later explicit authoring run to evaluate the resulting candidate anew, so that a resolved decision can still be implemented safely.
57. As a generation-contract reviewer, I want the contract checked through supported ambiguous and boundary inputs, so that another Agent can follow it without inventing target facts, steps, or exits.
58. As a generation-contract reviewer, I want contract qualification to remain a static walkthrough, so that fake projects and author-written targets do not become semantic oracles.
59. As a generated-target user, I want a target created later in a real project treated as a new ordinary candidate, so that contract approval cannot approve the target by proxy.
60. As a generated-target user, I want the target to receive its own fresh reviewer and separate verdicts, so that contract assumptions do not replace target evidence.
61. As a generated-target user, I want the target to pass its normal machine, Semantic Review, Representative Acceptance, and handoff gates before adoption, so that every real artifact uses the same Acceptance Standard.
62. As a project maintainer, I want the canonical runtime artifact accepted before its reference mirror is modified, so that a mirror cannot become the semantic oracle.
63. As a project maintainer, I want mirrors reviewed in one independent bounded batch, so that translation fidelity does not lengthen every canonical revision.
64. As a project maintainer, I want mirror failures to block Adoption without invalidating unchanged canonical evidence, so that only affected gates rerun.
65. As a qualification maintainer, I want one representative Shared Rule, Project-local Rule, Rule-generation contract, Shared Skill, Project-local Skill, and Skill-generation contract, so that all authoring classes are covered.
66. As a qualification maintainer, I want the ordinary Shared Skill and Skill-generation contract piloted first, so that the two critical orchestration paths prove the redesign before broader work.
67. As a qualification maintainer, I want the remaining canaries to start automatically after both Pilot candidates pass, so that a successful bounded Pilot does not add a manual scheduling gate.
68. As a qualification maintainer, I want each canary independently frozen and invalidated only by changed dependencies, so that one failure does not restart unrelated work.
69. As a qualification maintainer, I want a minimal Regression Corpus of demonstrated defects, so that future regressions are caught without exhaustive mutation testing.
70. As a reviewer, I want semantic omission, unsupported precision, broadened applicability, authoring-metadata leakage, and conflicting exits represented as focused Defect Cards, so that the known failure classes remain testable.
71. As a maintainer, I want Defect Cards counted within each candidate's bounded high-risk cases, so that regression testing does not create another evaluation layer.
72. As a maintainer, I want all required canaries and mirrors to pass before all-or-none Adoption, so that the repository never receives a half-qualified standard.
73. As a maintainer, I want full project tests, adapter checks, and diff integrity run at Adoption, so that distribution and repository boundaries are verified together.
74. As a maintainer, I want final changes left unstaged and uncommitted, so that I can inspect them before any publication.
75. As a maintainer, I want Matt, external, vendored, third-party, and unauthorized owners excluded, so that qualification cannot rewrite dependencies it does not own.
76. As a maintainer, I want only the named canaries changed during qualification, so that a validation exercise does not become a full repository rewrite.
77. As a maintainer, I want custom digests, evidence-closure archives, dual-author campaigns, 343-row prose matrices, and routine mutation testing excluded, so that evaluation cost remains proportional to risk.
78. As a maintainer, I want the final handoff to report exact commands, exits, verdicts, corrections, size changes, and untested surfaces, so that no persistent report file is needed.
79. As a maintainer, I want Matt-informed writing principles encoded in shared authoring mechanics, so that ordinary Rule and Skill work benefits from them without selecting or comparing external exemplars.
80. As an authoring Agent, I want transferable style patterns separated from artifact semantics, so that a polished rewrite cannot silently change behavior.
81. As a runtime Agent, I want action order, decision points, and completion criteria visible at the level where I need them, so that I do not search through unrelated reference material.
82. As a runtime Agent, I want branch-specific detail progressively disclosed behind precise pointers, so that the main path remains legible without hiding required instructions.
83. As a maintainer, I want duplicated meaning, decorative Markdown, no-op advice, and discoverable environment facts pruned from runtime prose, so that concise documents spend attention only on live obligations.
84. As a Rule and Skill author, I want parallel concepts expressed with aligned terminology and structure, so that switching artifact types does not impose an avoidable new mental model.
85. As a reviewer, I want expression quality judged through whole-artifact navigation and execution rather than prose snapshots, so that Matt-like clarity remains verifiable without freezing wording.
86. As a qualification maintainer, I want six independent reusable cases versioned under `tests/fixtures/write-rules-and-skills/`, so that each artifact class is reproducible without preserving run state.
87. As a generation-contract reviewer, I want static walkthrough cases for unclear intent, owner, target location, evidence conflict, and preservation risk, so that guidance completeness is tested without a fake target.
88. As a Project-local artifact reviewer, I want a small self-contained project only when repository facts affect behavior, so that local semantics are real without turning every case into a microproject.
89. As a Shared Rule reviewer, I want one representative context plus direct portability evidence by default, so that a single-project policy is not mislabeled as shared without doubling every Acceptance run.
90. As a Shared Skill reviewer, I want a second context only when portability is material and direct evidence cannot resolve it, so that hidden local assumptions are tested at the point of uncertainty.
91. As an Ordinary Artifact user, I want an isolated fresh Agent to apply the candidate to a representative task, so that Acceptance proves use rather than a reviewer's prediction.
92. As a reviewer, I want the Acceptance Runner to receive only runtime-visible candidate content, the task, and required context or tools, so that hidden answers cannot manufacture compliance.
93. As a reviewer, I want expected results, ledgers, diffs, author reasoning, findings, and prior case output hidden from the Runner, so that its observable result remains independent evidence.
94. As a maintainer, I want one Behavior Control only when a proposed instruction exists solely to change default Agent behavior and no observed failure establishes the need, so that no-op guidance is rejected without taxing factual artifacts.
95. As a maintainer, I want a rewrite's control to use the previously accepted artifact and a new artifact's control to omit the candidate, so that the comparison isolates the proposed guidance.
96. As a maintainer, I want one run per case by default and at most one confirmation rerun for an inconclusive or unstable result, so that variance is exposed without repeated sampling.
97. As a generation-contract maintainer, I want static Acceptance to start neither an Acceptance Runner nor target generation, so that the resolved latency problem stays resolved.

## Implementation Decisions

### Authoring Ownership and Routing

- One model-invoked SmartKit Skill owns the shared entry point and routes by semantic result rather
  than current filename.
- The router loads exactly one lifecycle reference (`ordinary-artifact.md` or
  `generation-contract.md`) and one semantic-type reference (`rule.md` or `skill.md`). For an
  ordinary artifact, its own type selects the semantic reference; for a generation contract, the
  future target type selects it.
- `ordinary-artifact.md` owns Shared versus Project-local classification and actual-use Acceptance.
  `generation-contract.md` owns generation evidence, ambiguity stops, static walkthrough, and the
  later handoff of a real target to ordinary validation.
- `rule.md` and `skill.md` each combine that type's authoring requirements with its type-specific
  Acceptance cases. Do not create generation-specific leaf references until real obligations cannot
  be expressed by the two selected references.
- Policy plus procedure becomes two separately owned artifacts.
- The shared contract is cross-project within the SmartKit architecture. It discovers and obeys
  active project Rules, host mechanics, configuration, and owner contracts rather than copying
  their facts.
- Project language, mirror, source-authority, distribution, concrete command, and host-syntax facts
  remain project-owned and do not appear in the reusable Skill.
- Runtime artifacts contain only schema-required or behavior-changing instructions that cannot be
  derived from a reliably loaded owner.
- Working evidence, provenance, semantic ledgers, validation results, and review records stay
  outside runtime prose.

### Understanding and Candidate Construction

- Implementation Readiness is required before the first candidate write and covers outcome,
  preserved semantics, non-goals, owner, authorized surfaces, dependencies, risks, validation
  seams, and material unknowns.
- When a proposed instruction's sole supported purpose is to change default Agent behavior and no
  observed failure already establishes that need, run one isolated Behavior Control before writing.
  Use the previously accepted artifact for a rewrite or no candidate for a new artifact; keep the
  raw result for review. Do not run a control for policy authority, project facts, reference
  material, Generation Contracts, or behavior already supported by observed failure evidence.
- Rerun the same case with the candidate. If the control already produces the required behavior,
  omit the no-op instruction unless separate accepted evidence requires an explicit policy.
- The Agent asks only when evidence still permits materially different policies, actions, owners,
  write targets, exits, authority, or side effects.
- The semantic ledger uses one independently changeable obligation per row and resolves one owner
  plus one preserve, change, add, move, or retire disposition.
- A candidate is synthesized from the whole ledger. The old artifact is omission evidence, not the
  new outline.
- Supported decisions and safety boundaries are preserved; stale, duplicated, contradictory,
  transitional, and misplaced content is removed.
- Markdown is semantic structure. Headings, lists, tables, emphasis, blocks, and links are used only
  when they improve discovery, interpretation, ordering, or execution.
- Concision is optimized only after semantic completeness, executability, and one unambiguous
  interpretation pass.

### Expression and Information Design

- Current first-party behavior, accepted intent, project authorities, and real owner surfaces remain
  the semantic sources of truth. Matt-informed mechanics shape expression but never supply artifact
  semantics.
- Encode stable expression techniques once in shared writing or authoring guidance. Ordinary
  authoring applies that guidance without discovering, selecting, or comparing Matt exemplars, and
  never copies domain behavior, repository facts, commands, or ownership assumptions.
- Separate ordered steps from consulted reference. Keep the main path and its completion criteria
  visible; disclose branch-only reference behind a pointer whose wording states when to load it.
- Co-locate a concept's definition, rules, and caveats. Use headings, lists, tables, emphasis,
  blocks, and links only when they expose hierarchy, sequence, comparison, state, or routing.
- Prefer a stable leading term over repeated explanations, and prefer positive target behavior over
  negation when both express the same boundary.
- Remove duplicated meaning, no-op instructions, stale sediment, and cheap environment lookups.
  Retain a lookup only when finding it at runtime is unreliable or materially expensive.
- Align terminology, phase names, heading intent, and sentence shape across Rule and Skill guidance
  where meanings overlap. Preserve artifact-specific structure where policy and procedure differ.
- Treat unchanged or reduced size as the normal expectation. Growth requires a distinct supported
  semantic obligation, not additional authoring metadata or explanatory ceremony.

### Rule and Skill Completeness

- A Rule resolves its class, owner, strength, scope, applicability, precedence, exceptions,
  boundaries, and outcomes. Observable cases reject the nearest false positive and false negative.
- A Skill resolves its actor, trigger, inputs, preconditions, start, actions, outcome, owner,
  boundaries, completion, stop, failure, recovery, validation, resources, and handoff.
- Every Skill path has exactly one prioritized exit; completion cannot bypass required validation,
  cleanup, preservation, or handoff.
- An owned script is introduced only when the work is repeated, fragile, and deterministic, and
  its complete executable contract is stated.
- A generation contract defines complete target packaging, policy or job, schema, owner split, and
  write target. It stops rather than guessing when target evidence remains ambiguous.

### Unified Acceptance Standard

- The Acceptance Standard consists of evidence-backed authoring, focused machine validation, fresh
  Semantic Review, Representative Acceptance, and explicit handoff.
- Every Ordinary Artifact, Generation Contract, and authoring-workflow candidate uses the same
  gates. Acceptance Portfolios vary by artifact risk but cannot replace or weaken a gate.
- Machine validation proves only structured or executable facts. Natural-language semantics are
  proved by whole-artifact review and representative use.
- Candidate Revision means the complete current content state. Semantic changes invalidate every
  machine, Review, and Acceptance result that depends on the old state.
- Candidate writes freeze while Candidate Review runs. Mutation discards its verdicts and stops the
  run without automatic restart.
- One fresh reviewer receives one bounded Review Packet, performs Semantic Review first, then runs
  the artifact-specific Acceptance only after Semantic Review passes, and returns separate verdicts.
- When Readiness required a Behavior Control, include its selected task and raw result in the Review
  Packet without converting the result into an author-written semantic conclusion.
- For an Ordinary Artifact, the reviewer sends the selected portfolio to one isolated Acceptance
  Runner. Every case starts from its declared frozen input and does not inherit another case's
  result. The Runner receives the candidate exactly as runtime would expose it, the tasks, and only
  the required context or tools; it receives no ledger, expected result, diff, author reasoning,
  finding, prior run output, or other reviewer-only material.
- The Runner must make the decision, produce the output, or use the public entry required by the
  task. Reciting the candidate or predicting what an Agent would do is not Acceptance evidence. The
  reviewer, not the Runner, compares observable work and artifacts with accepted evidence.
- Run each case once by default. A reviewer may rerun one case once only when its result is
  inconclusive or unstable; use a new isolated Runner, report both results, and fail divergent
  behavior instead of selecting the favorable sample.
- Each candidate receives its own fresh reviewer. Independent Candidate Reviews may run in
  parallel, but their packets, revisions, counterexamples, findings, and verdicts remain separate.
- Findings from both gates are aggregated before action. Any decision-required finding stops;
  otherwise all uniquely forced findings are fixed once.
- A different fresh Closure Reviewer receives the corrected candidate, first-round findings,
  revalidation evidence, and affected cases. Closure has one attempt and cannot start another
  automatic correction.
- A user decision ends the current automatic run. A later explicit authoring run may evaluate the
  resulting candidate from the beginning.
- Reviewer unavailability, candidate mutation, machine failure, decision-required findings, and
  Closure failure each have explicit stop and handoff behavior.

### Generation Contracts

- A generation contract is an instruction artifact, not a generated target. It defines how another
  Agent discovers target evidence, resolves packaging and ownership, preserves existing semantics,
  writes the complete target, stops on material ambiguity, validates the result, and hands it off.
- Qualification reviews that guidance statically against two to four supported high-risk inputs.
  The walkthrough fails when another Agent would need to invent a target fact, condition, step,
  owner, path, recovery, or exit.
- Static Generation Contract Acceptance is performed by the fresh reviewer and starts neither an
  Acceptance Runner nor target generation.
- Contract qualification does not create a target or require a fake project. Deterministic scripts
  or renderers owned by the contract still use their normal machine tests and real public entry
  points.
- When the contract later produces a target in a real project, that target becomes a new ordinary
  Rule or Skill candidate. It runs the normal Acceptance Standard with a fresh reviewer, defaults to
  a reviewer different from the contract reviewer, and cannot inherit the contract's verdicts.
- The contract completes when its own machine validation, Semantic Review, static Acceptance, and
  handoff pass. It does not claim that an uncreated future target has passed.

### Qualification and Adoption

- Qualification is a task-specific campaign, not a second Skill or a different quality standard.
- Qualification creates no persistent workspace, copied revision tree, custom digest, or report.
- Candidate state uses the active checkout; one Task Worktree is used only when dirty state,
  concurrent writes, or all-or-none isolation genuinely requires it.
- Review Packets are assembled just in time. Temporary mutable case copies are removed after
  handoff.
- Committed evaluation cases are stable test inputs, not a qualification workspace or retained
  Candidate Revision. They contain no generated answers, verdicts, run reports, or Acceptance
  sandboxes.
- Six representative artifact classes cover Shared and Project-local Rules, Shared and
  Project-local Skills, and both generation-contract types.
- The Pilot uses one ordinary Shared Skill and one Skill-generation contract. The remaining four
  canaries start automatically after both Pilot candidates pass Semantic Review and Acceptance.
- Independent canaries may run in parallel, freeze separately, and invalidate only when their
  content or governing dependencies change.
- Five focused Defect Card classes exercise semantic omission, unsupported precision, broadened
  applicability, authoring-record leakage, and conflicting exits.
- Defect Cards remain inside the two-to-four-case portfolio and are promoted only when they detect a
  real, durable regression.
- Canonical runtime candidates are accepted before project reference mirrors are updated.
- Mirror review is a separate bounded batch. Mirror failure blocks Adoption but does not invalidate
  unchanged canonical evidence.
- Adoption is all-or-none after every canary, Defect Card, applicable mirror, size comparison, and
  repository verification passes.
- Publication, installation, commit, push, and pull-request creation remain separate owner actions.

## Testing Decisions

- Prefer the highest existing seam: the real public entry point for executable behavior, the
  project's supported validation commands for structured facts, and whole-artifact application for
  natural-language semantics.
- Candidate-focused machine validation covers changed schema, registration, resource reachability,
  generated relationships, filesystem effects, script results, state transitions, and process
  exits.
- The complete repository suite, Agent adapter drift, MCP adapter drift, and diff integrity run
  once at Adoption and after changes to the Acceptance Standard itself.
- Tests may assert schemas, formal identifiers, resource and registration relationships, generated
  outputs, filesystem effects, state transitions, exit behavior, and declared repository
  boundaries.
- Tests must not snapshot ordinary prose, translated wording, physical line wrapping, complete
  heading lists, or author-written semantic outcome tables.
- English canonical semantics are reviewed first under the project's current language policy.
  Reference mirrors are checked afterward for one-to-one order, Markdown structure, paths,
  commands, identifiers, code blocks, and behavior; they never repair the canonical source.
- Rule Acceptance covers included and excluded applicability, affected boundaries, exceptions,
  precedence, and conflicts. An isolated Runner must apply the loaded Rule to the task and produce
  an observable decision or action rather than explain the Rule academically.
- Skill Acceptance covers normal completion and the highest-risk applicable stop, failure,
  recovery, handoff, and coincident-exit paths. An isolated Runner must perform the job from its
  trigger using only runtime-visible inputs.
- Scripted Skills are exercised through their real public entry. Supported platforms that cannot be
  run are reported as untested.
- Generation-contract Acceptance statically walks the complete guidance against the highest-risk
  supported ambiguity, ownership, placement, conflict, preservation, and exit cases. It does not
  generate or grade a fake target.
- A real target created by a generation contract later enters the ordinary Rule or Skill portfolio
  and receives a fresh Candidate Review before adoption.
- Shared Rule Acceptance uses one representative traceable context plus direct evidence that the
  policy does not depend on project-local facts. Add a second context only when portability is
  material and direct evidence cannot establish it; the portfolio still covers the relevant
  applicability, exclusion, boundary, exception, precedence, and local-conflict behavior.
- Shared Skill Acceptance uses one representative traceable context plus direct portability
  evidence. Add a second context only for a material unresolved portability claim. Owned executable
  resources still use their real public entry points.
- Project-local Rule and Skill cases may include a small self-contained project when local Rules,
  configuration, files, or commands affect the result.
- `tests/fixtures/write-rules-and-skills/` stores six independent case definitions with requests,
  evidence, initial state, structured Acceptance cases, and only the small project inputs a case
  needs. Ordinary cases declare isolated-runner Acceptance; Generation Contract cases declare
  static walkthrough. Structured expected results remain reviewer-only. The fixtures store no
  generated candidate, verdict, report, mutable run state, or exact expected prose.
- Every ordinary candidate uses two to four highest-risk supported cases. Exhaustive
  natural-language matrices are prohibited.
- Each candidate compares line, word, and byte size to its baseline. Growth is acceptable only when
  a distinct supported obligation requires it; there is no fixed numeric limit.
- The redesigned orchestration is first tested with an ordinary Shared Skill and a
  Skill-generation contract. This covers ordinary application, non-completion exits, generation
  evidence, ambiguity stops, static contract walkthrough, and the future-target handoff boundary.
- A good semantic test exposes a concrete case in which the same supported facts would otherwise
  produce two outcomes, no outcome, an invented step, or an unsupported owner. It does not merely
  find a matching sentence.
- Semantic Review uses the candidate's accepted evidence as the sole semantic oracle and evaluates
  the observable result of the active writing mechanics: information hierarchy, visible action
  order, progressive disclosure, co-location, completion criteria, terminology alignment, positive
  phrasing, pruning, and Markdown purpose. It does not require similarity to an external exemplar.
- Representative Acceptance requires a fresh Agent to locate the artifact's applicability or
  trigger, main path or outcome, owner boundaries, and relevant exits without author explanation.
  Required branch material may live behind a precise pointer; unexplained searching or invented
  navigation is a failure.
- A Behavior Control is conditional evidence, not a universal RED phase. It is required only for a
  behavior-shaping instruction whose need is otherwise unsupported; one accepted-version or
  no-candidate run plus the matching candidate run is sufficient unless the result is inconclusive.
- Style findings must name an observable reading or execution cost and a supported correction.
  Personal wording preference alone cannot fail a candidate.

## Out of Scope

- Rewriting every first-party Rule or Skill as part of qualification.
- Modifying Matt Skills, external Skills, vendored Skills, third-party artifacts, or unauthorized
  owners.
- Copying Matt wording, headings, commands, domain behavior, or repository assumptions as a
  template, or treating Matt artifacts as semantic authorities.
- Moving project-specific language, mirror, source-authority, command, or distribution facts into
  the cross-project authoring Skill.
- Creating a separate qualification Skill or a second Acceptance Standard.
- Persisting a qualification workspace, revision tree, evidence archive, or qualification report.
- Requiring custom candidate digests when the active project has no such protocol.
- Using dual authors, eight candidate bundles, 343-row natural-language matrices, evidence-closure
  archives, or routine mutation testing for ordinary authoring.
- Requiring Behavior Control for policy authority, project facts, reference material, Generation
  Contracts, or already observed failures; running five-sample wording campaigns or selecting a
  favorable result from divergent Runner outputs.
- Turning Defect Cards or semantic expectations into brittle sentence or heading assertions.
- Treating a fake generated target, prepared answer, or invented project as proof that a generation
  contract is complete.
- Automatically restarting review after candidate mutation, a user decision, Closure failure, or a
  failed second run.
- Committing, publishing, installing, pushing, opening a pull request, or expanding qualification
  beyond the accepted canaries without separate authorization.
- Adding compatibility aliases, migrations, fallbacks, or retired-contract behavior.

## Further Notes

- The initiating requirement is better first-party Rule and Skill writing: preserve existing
  semantics while learning Matt-like expression, information hierarchy, and meaningful Markdown.
  The unified Acceptance Standard and bounded qualification design were introduced later to make
  that outcome trustworthy and affordable.
- The durable architecture decision is the unified Acceptance Standard with different
  risk-matched Portfolios. Campaign-specific canaries, scheduling, Defect Cards, and Adoption scope
  remain task decisions.
- The earlier authoring-contract verdict predates the corrected Matt-expression requirement and is
  not evidence that the current candidate satisfies this Spec. Runtime contract revision and
  qualification remain deferred until the maintainer authorizes that next scope.
- The previous persistent qualification directory was removed. No qualification report replaces
  it.
- Earlier Pilot attempts are defect evidence only. The static-contract, fixture-backed ordinary
  Shared Skill and Skill-generation Pilot has not started.
- Repository changes remain unstaged and uncommitted unless separately authorized.
