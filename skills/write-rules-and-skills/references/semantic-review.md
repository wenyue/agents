# Semantic Review

This reference owns the review packet, Semantic Review gate, and reviewer verdicts. The parent
Skill owns gate order, reviewer isolation, finding-class handling, correction, and handoff. The
selected lifecycle and semantic-type references own the applicable counterexamples and Acceptance
portfolio.

## Give the bounded packet

Give the reviewer:

- the accepted outcome and semantic ledger;
- the selected task and raw Behavior Control result when Readiness required one;
- the complete candidate, owned resources, and loading or distribution surfaces;
- governing evidence and applicable references; and
- exact machine-validation results and untested surfaces.

Exclude the diff, author reasoning, suspected defects, intended fixes, and expected verdicts.

## Try to falsify the candidate

Read the whole candidate and try to falsify it with two to four of the highest-risk supported
counterexamples. Return a distinct Semantic Review `PASS` or `FAIL`.

Every blocking finding names its gate, evidence, concrete counterexample, and one shared finding
class. For `decision-required`, also name the exact unresolved choice, its decision owner, and the
evidence for each materially different supported outcome; the number of findings is not such
evidence.
