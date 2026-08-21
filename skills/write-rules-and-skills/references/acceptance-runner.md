# Acceptance Runner

This reference owns the common isolation and execution protocol for Ordinary Artifact Acceptance.
The parent Skill owns when Acceptance starts and who may serve as Runner. The selected lifecycle
and semantic-type references own the representative cases and scope-specific pass conditions.

## Give the isolated input

Give the Runner the frozen candidate as runtime would expose it, the triggered task or policy
application, the selected case input, and only the context or tools that case requires. Keep the
expected result, semantic ledger, diff, author reasoning, findings, reviewer instructions, and
prior case output outside the Runner's context.

Start every case from its declared frozen input. Do not let one case's result become another case's
input. When Readiness required a Behavior Control, compare its raw result with the matching
candidate run after both complete; expose neither result to the other Runner.

## Apply the artifact

Before execution, create a unique Runner-owned temporary case directory in the project workspace
outside candidate-owned files. Keep all Acceptance-created artifacts there and give child
processes and tools its absolute path. Report any required tool unable to honor the directory as
untested instead of writing elsewhere. After the reviewer captures the case result, delete the
case directory; if safe cleanup fails, report its retained path.
Use the real public job entry or policy-application seam when available. Run owned deterministic
resources through their public entries. The Runner must apply the candidate; an academic
explanation or reviewer walkthrough is not Acceptance evidence.

Report supported execution that the environment cannot run as untested. A controlled walkthrough
may explain that surface but cannot replace isolated application or establish machine PASS.

Run each case once. Repeat an inconclusive or unstable case at most once with a new isolated
Runner; divergent outcomes fail. Return the observed result and tested or untested surfaces to the
reviewer without deciding against an undisclosed expected result.
