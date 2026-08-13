# SmartKit Rule and Skill Authoring Contract

Status: ready-for-agent

## Problem Statement

SmartKit needs one cross-project authoring workflow that helps an Agent fully understand a requested
Rule or Skill before writing it, preserves every supported semantic obligation, avoids inventing
policy, and produces a concise artifact that another Agent can apply without hidden context.

The current authoring workflow mixes reusable SmartKit architecture with facts that belong to the
active project. It has also accumulated proof machinery that attempts to turn natural-language
policy into exhaustive machine assertions. During evaluation this produced repeated full rewrites,
hundreds of author-defined scenarios, self-authored policy oracles, stale reviews, and long feedback
loops without providing reliable semantic proof. Generated artifacts became longer because evidence,
ownership metadata, and review records leaked into runtime prose.

Repository tests compound the problem when they pin exact prose, line wrapping, or complete heading
lists. Such assertions make harmless editing expensive while still failing to prove that a Rule or
Skill preserves its intended behavior.

SmartKit maintainers need a bounded authoring and validation contract. It must retain strict semantic
review while separating machine-verifiable repository behavior from Agent-reviewed natural-language
meaning. It must also keep project-specific facts in project-owned Rules, configuration, and owner
surfaces rather than embedding them in a reusable Skill.

## Solution

Replace the current authoring workflow with a lean routed SmartKit Skill. The shared entry point owns
understanding, Rule-or-Skill routing, semantic preservation, write authorization, validation order,
fresh review, representative Acceptance, and terminal outcomes. Specialized references own only the
different structures of Rule policy and Skill procedure.

Before writing, the Agent inspects the target artifact, applicable project Rules, current behavior,
configuration, owner surfaces, tests, and distribution mechanisms. It creates a temporary semantic
ledger containing one row per independently changeable obligation. The Agent stops only when missing
evidence permits materially different policies, actions, owners, or exits; uniquely determined facts
may be established from stable implementation, configuration, or tests.

Runtime artifacts contain only the governing schema and instructions that change an Agent decision,
action, or observable outcome. Evidence records, review metadata, provenance inventories, and
verification results stay outside runtime prose. Reusable SmartKit architecture may be stated by the
authoring Skill, while language policies, mirror relationships, concrete paths, project commands,
ownership declarations, and other project facts remain owned by the active project.

Machine validation checks structured and executable behavior: packaging schema, registered
resources, generated relationships, filesystem effects, script results, and repository-supported
tests. It does not claim to prove the meaning of natural-language policy. A fresh reviewer receives
the accepted intent, semantic ledger, complete candidate, governing evidence, and validation results,
then reviews the whole artifact and representative counterexamples. One uniquely forced correction
may be applied automatically; a second failed review or any decision-required finding returns to the
user.

Validate the workflow with exactly six representative canary classes: Shared Rule, project-local
Rule, Rule-generation contract, ordinary Shared Skill, scripted Shared Skill, and Skill-generation
contract. Each canary uses a small set of high-risk counterexamples. The two generation contracts
must each author one complete target and have that target independently reviewed. All six temporary
candidates must pass before any of them is adopted. The resulting repository change remains
uncommitted for human review.

## User Stories

1. As a SmartKit user, I want an Agent to understand my requested outcome before writing, so that it
   does not implement an attractive but incorrect interpretation.
2. As a SmartKit user, I want unresolved choices surfaced only when they can materially change the
   result, so that I am not asked redundant questions.
3. As a SmartKit user, I want an already authorized and uniquely supported plan to continue without
   another confirmation, so that the workflow remains efficient.
4. As a project maintainer, I want existing Rule and Skill semantics preserved during rewrites, so
   that clearer wording does not silently change behavior.
5. As a project maintainer, I want each independently changeable obligation recorded once, so that
   omissions and unauthorized retirements are reviewable.
6. As a project maintainer, I want conditions, exceptions, owners, and exits separated only when
   they can change independently, so that the ledger remains useful without becoming a sentence-level
   matrix.
7. As a project maintainer, I want unsupported policies and thresholds rejected, so that an Agent
   cannot invent precision merely to make a document appear testable.
8. As a project maintainer, I want SmartKit-wide authoring architecture separated from active-project
   facts, so that the same Skill works correctly in different repositories.
9. As a project maintainer, I want the authoring Agent to read my applicable project Rules and owner
   surfaces, so that local policy remains authoritative.
10. As a project maintainer, I want missing project facts derived only from stable evidence, so that
    undocumented but deterministic behavior does not cause unnecessary blocking.
11. As a project maintainer, I want ambiguous ownership or generation relationships to stop before
    writes, so that the Agent does not mutate the wrong source.
12. As a Rule author, I want the workflow to distinguish persistent policy from triggered procedure,
    so that a Rule does not become an imperative runbook.
13. As a Skill author, I want the workflow to model actor, inputs, preconditions, actions, recovery,
    stops, failures, completion, and handoff, so that every executable branch has an outcome.
14. As an author of policy plus procedure, I want the workflow to create separately owned Rule and
    Skill artifacts, so that one document does not mix incompatible responsibilities.
15. As a Rule author, I want Rule-specific applicability, precedence, exceptions, and condition
    boundaries reviewed, so that the policy resolves supported cases consistently.
16. As a Skill author, I want coincident failures and stop conditions prioritized, so that the same
    state cannot produce two terminal outcomes.
17. As a maintainer, I want evidence and review metadata kept out of runtime prose, so that Rules and
    Skills stay concise and cheap for Agents to consume.
18. As a maintainer, I want every additional runtime line to affect a decision, action, or outcome,
    so that template-shaped metadata does not inflate artifacts.
19. As a maintainer, I want generated target schemas complete, so that a generation contract cannot
    replace required runtime meaning with a pointer back to the authoring workflow.
20. As a maintainer, I want generation to stop when evidence permits materially different target
    policies or procedures, so that target authors do not guess.
21. As a maintainer, I want machine validation limited to objectively executable or structured
    behavior, so that green tests do not masquerade as semantic proof.
22. As a maintainer, I want a fresh reviewer with no author reasoning history, so that review tries
    to falsify the complete candidate rather than confirm the intended edit.
23. As a maintainer, I want the reviewer to compare the candidate directly with source evidence, so
    that a ledger cannot repair missing runtime meaning.
24. As a maintainer, I want one uniquely forced correction allowed after a failed review, so that
    mechanical defects can be resolved without an open-ended loop.
25. As a maintainer, I want a second failed review to stop and report all blockers, so that authoring
    cannot run indefinitely.
26. As a maintainer, I want decision-required findings returned immediately, so that automated fixes
    do not create new policy or authority.
27. As a test maintainer, I want repository tests to assert schemas, resources, registrations,
    generation, filesystem effects, and exits, so that they protect observable contracts.
28. As a test maintainer, I want ordinary prose, line wrapping, and complete heading sequences kept
    out of string snapshots, so that harmless editorial changes do not break tests.
29. As a reviewer, I want natural-language quality proven through whole-artifact review and canary
    Acceptance, so that semantic defects receive counterexamples instead of substring checks.
30. As a SmartKit maintainer, I want one representative Shared Rule canary, so that reusable policy
    authoring is exercised without a repository-specific shortcut.
31. As a SmartKit maintainer, I want one project-local Rule canary, so that active-project ownership
    and policy can be preserved without entering the reusable contract.
32. As a SmartKit maintainer, I want one Rule-generation canary to produce a complete target Rule, so
    that generation quality is tested beyond Markdown structure.
33. As a SmartKit maintainer, I want one ordinary Shared Skill canary, so that a concise conditional
    workflow can be authored and reviewed.
34. As a SmartKit maintainer, I want one scripted Skill canary, so that prose remains aligned with
    immutable executable behavior and real exit codes.
35. As a SmartKit maintainer, I want one Skill-generation canary to produce a complete target Skill,
    so that branch and exit semantics are tested in a representative target.
36. As a SmartKit maintainer, I want two to four high-risk counterexamples per canary, so that
    verification stays bounded while targeting likely false positives and omissions.
37. As a SmartKit maintainer, I want semantic-omission, unsupported-policy, over-broad-applicability,
    evidence-metadata, and conflicting-exit mutants rejected, so that the reviewer demonstrates useful
    fault detection.
38. As a SmartKit maintainer, I want all six temporary candidates accepted before repository adoption,
    so that the repository never contains a partially migrated authoring model.
39. As a SmartKit maintainer, I want candidate size compared with its baseline, so that unexplained
    document growth is treated as a quality defect.
40. As a SmartKit maintainer, I want the final six-canary result left uncommitted, so that I can
    perform a human review before any publication decision.

## Implementation Decisions

- Keep one cross-project SmartKit authoring entry point that routes by semantics to a Rule-specific
  or Skill-specific reference. Read both references only when the accepted result genuinely needs two
  separately owned artifacts.
- Treat SmartKit authoring concepts as reusable architecture. Obtain active-project schema,
  ownership, source authority, generation relationships, distribution surfaces, and validation from
  applicable project Rules, configuration, owner contracts, and stable evidence.
- Do not encode language policy, localization policy, repository paths, repository commands,
  project-specific ownership, external-source classifications, or host invocation syntax in the
  reusable authoring contract.
- Use six ordered stages: understand current intent and mechanism; build the semantic preservation
  boundary; resolve or stop on material uncertainty; author the smallest complete candidate; run
  project-supported machine validation; perform fresh semantic Review followed by representative
  Acceptance.
- For new artifacts, record requirements; for updates, record preservation. One row represents one
  independently changeable semantic obligation. Separate rows when the predicate, exception, owner,
  action, recovery, or exit can change independently. Do not split mere wording choices.
- Keep the ledger, evidence notes, validation output, review record, and Acceptance record outside the
  runtime artifact.
- Include a runtime statement only when it belongs to the governing artifact schema or changes an
  Agent decision, action, or observable outcome and cannot be uniquely derived from a reliably loaded
  owner surface.
- Let the Rule reference own policy fields, applicability, precedence, exceptions, boundaries,
  condition-to-outcome reasoning, and generated-Rule completeness.
- Let the Skill reference own actor, inputs, preconditions, start, ordered and conditional actions,
  recovery, stop, failure, completion, handoff, resources, branch-to-exit reasoning, and generated-
  Skill completeness.
- Preserve the current target's required packaging schema by applying the active SmartKit and host
  mechanics. Do not duplicate change-prone schema enumerations or host-specific invocation syntax in
  the authoring prose.
- Machine Proof may validate only facts independently derivable from structured inputs or executable
  behavior. It must not simulate an Agent's interpretation of natural-language policy through
  keyword checks, section mappings, copied expectations, or author-written policy oracles.
- Require one fresh reviewer after machine validation. The reviewer receives the accepted outcome,
  semantic ledger, complete candidate, relevant governing evidence, and exact validation results,
  but not the author's reasoning, suspected defects, or expected verdict.
- Permit one automatic correction only when accepted intent and verified evidence force exactly one
  in-scope change without adding policy, authority, behavior, or side effects. Rerun affected
  validation and use another fresh reviewer. Stop on any decision-required finding or a second failed
  review.
- Do not require a custom artifact digest, exhaustive sentence-level scenario matrix, dual-author
  comparison, or mutation suite for routine authoring. Candidate changes after Review invalidate that
  Review and require another validation and Review pass.
- Reserve dual-author comparison, large evidence closures, exhaustive matrices, and broader mutation
  campaigns for explicit high-risk evaluation of the authoring workflow, not ordinary Rule or Skill
  production.
- Add project-owned testing policy that prohibits ordinary natural-language sentence, line-wrap, and
  complete-heading snapshots. Exact text assertions remain valid only when the text is itself a
  structured external protocol value.
- Evaluate exactly six canary classes in temporary candidate space. Each uses two to four high-risk
  counterexamples. Generation canaries additionally create and independently review one complete
  generated target.
- Adopt the six canaries as one repository change only after every candidate passes its required
  machine validation, semantic Review, and representative Acceptance.
- Report line, word, and byte counts against each baseline. Growth without a distinct supported
  semantic obligation is a blocking quality defect; no fixed numeric size threshold is introduced.
- Leave the completed change unstaged and uncommitted for maintainer review.

## Testing Decisions

- Use one highest-level behavioral seam: the authoring contract receives an accepted outcome and
  current evidence, produces a candidate, sends it through fresh semantic Review, and exercises it in
  representative canary contexts.
- Machine tests assert structured behavior only: registration and reference reachability, valid
  packaging schema, owned-resource existence, generated relationships, filesystem effects, script
  behavior, state transitions, and process exits.
- Do not use sentence-presence tests, physical line wrapping, translated prose, or complete heading
  lists as proof of natural-language quality. Review such prose as a whole artifact against accepted
  intent and project evidence.
- Retain minimal routing checks that demonstrate the shared entry point can select Rule authoring,
  Skill authoring, or two separately owned artifacts.
- Validate the Shared Rule canary with high-risk cases around applicability, unsupported precision,
  exceptions, and project precedence.
- Validate the project-local Rule canary with high-risk cases around owner-edit selection, generated
  versus canonical sources, project-specific evidence, and unowned writes.
- Validate the Rule-generation contract by having a fresh target author create one complete Rule from
  controlled evidence, followed by an independent reviewer applying representative included,
  excluded, ambiguous, and boundary cases.
- Validate the ordinary Shared Skill canary with normal completion, missing prerequisite, routed
  dependency, recoverable failure, and scope-expanding failure as applicable to its accepted job.
- Validate the scripted Skill canary through its real public invocation and focused executable tests.
  Confirm that prose does not invent categories, fallbacks, commands, or exits absent from the owned
  implementation.
- Validate the Skill-generation contract by having a fresh target author create one complete Skill,
  followed by an independent reviewer walking its main path, one stop, one failure, one recovery, and
  at least one coincident condition.
- Seed five focused defect classes across the canary set: omitted semantic obligation, unsupported
  policy, broadened applicability, evidence-only runtime metadata, and missing or conflicting exit.
  Each mutant must receive a failing semantic Review with a concrete counterexample.
- Run at most two Review rounds per logical candidate. The first failure may trigger one uniquely
  forced correction; the second failure stops the candidate.
- Compare every accepted candidate's line, word, and byte counts with its baseline and require the
  reviewer to explain any supported increase.
- After all six temporary canaries pass, adopt them together and run the repository's complete test
  suite, generated-adapter drift checks, and diff-integrity check.
- Treat unavailable platform-specific execution as explicitly untested rather than passing. Report
  exact commands, final exits, relevant failures, and remaining untested surfaces.

## Out of Scope

- Rewriting every first-party Rule and Skill in the repository.
- Modifying Matt-authored, external, vendored, or otherwise unapproved artifacts.
- Encoding the current repository's language, localization, ownership, path, command, or distribution
  facts in the reusable authoring Skill.
- Treating project documentation mirrors as runtime sources or using them to repair missing runtime
  semantics.
- Proving natural-language meaning with substring checks, heading snapshots, copied matrices,
  hard-coded outcome allowlists, or author-written policy interpreters.
- Requiring exhaustive sentence-level scenarios, custom bundle hashing, or two independent authors
  for every ordinary Rule or Skill change.
- Automatically fixing a decision-required finding or continuing after a second failed review.
- Writing back only a subset of the six accepted canaries.
- Committing, publishing a release, or expanding from the six canaries to a repository-wide rewrite.

## Further Notes

- Previous temporary evaluations remain useful only as defect examples. They demonstrated metadata
  leakage, semantic narrowing, omitted owners and exits, stale reviews, self-authored oracles, and
  excessive proof scope; their candidate prose is not an implementation source.
- The repository currently contains an unaccepted authoring-contract rewrite. Implementation begins
  by restoring that scope to its accepted baseline before synthesizing the new contract from this
  specification.
- The six canaries are an evaluation boundary, not a migration commitment for the remaining
  repository artifacts. Human review decides whether later work should expand the new model.
