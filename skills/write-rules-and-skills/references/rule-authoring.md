# Rule authoring

A Rule is **one policy with one owner and one meaning**. This branch owns Rule classification,
policy boundaries, strength, scope, distribution, and generation contracts.

## Pin the policy

Pin the policy, owner, strength, scope, applicability, precedence, exceptions, boundaries, and
outcome. Every applicable field must have one explicit value; a missing field needs a verified
reason that it does not apply.

Choose one class:

| Condition | Class | Contract |
| --- | --- | --- |
| One repository owns and directly applies the policy | Project-local Rule | State final policy from verified repository facts. Keep related requirements and exceptions in the narrowest project Rule that owns them. |
| A distributed Rule directly applies stable policy across repositories | Shared Rule | State only stable cross-repository policy, semantic target conditions, supported exceptions, and project-local precedence. Leave concrete implementation and narrower decisions local. |
| A distributed artifact authors a complete target-owned Rule | Shared Rule-generation contract | Separate the authoring workflow from the complete target-owned Rule. Define evidence, review, acceptance, and handoff without inventing target policy. |

Removing local details does not make a Rule shared. Use the shared class only when the policy itself
is stable across repositories. The policy is pinned when its class and every contract field have one
supported interpretation.

## Extend the evidence

In addition to the shared evidence, collect:

- the requested strength, scope, precedence, exceptions, and excluded policy responsibilities;
- the owning Rule family, broader and more-specific Rules, enforcement points, and generated owner;
- for a project-local Rule, every repository fact and module relationship needed to apply it;
- for a shared Rule, representative repositories, the stable cross-repository policy, and supported
  project-local overrides; and
- for a generation contract, representative target Rule families, precedence systems, generation
  surfaces, and validators.

Evidence is sufficient only when every policy choice and repository claim that could affect
application has support. Keep reusable procedures in Skills.

## Author the policy

- Lead with the governing policy. Co-locate each condition with its required outcome and exceptions.
- Stress-test every threshold, classification, and condition-to-outcome mapping with its nearest
  false positive. State every predicate needed to reject that case; labels such as `valid`,
  `control`, or `fixed point` do not carry an unstated prerequisite.
- Represent every current requirement once in the narrowest Rule that owns it. A broader Rule must
  not duplicate or silently override a more-specific Rule.
- Use observable conditions and outcomes. Move an ordered execution procedure into a Skill unless
  this is a generation contract whose authoring order changes the result.

For a Rule, headings represent stable policy regions or genuine applicability branches. Use a
numbered list only for an ordered Rule-generation sequence whose order changes the result. A policy
checklist names the subject, required action or property, and observable result.

## Shape the Rule

Start every final Rule with:

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One sentence naming the Rule's owned responsibility.
```

Add `Boundaries`, `Exceptions`, or `Precedence` only when the owned policy needs them. A generation
contract keeps its generation evidence, complete target content, review, acceptance, and handoff
independently discoverable.

## Whole-Rule Gate

In addition to the Whole-Artifact Gate, the Rule passes only when:

- its class, owner, strength, scope, applicability, precedence, exceptions, and boundaries are
  explicit or verifiably inapplicable;
- every threshold, classification, and condition-to-outcome mapping rejects its nearest false
  positive without relying on an undefined label or implicit predicate; and
- another Agent can determine the required outcome without inventing an execution procedure.

## Prove the Rule

- For a project-local Rule, verify concrete claims, enforcement points, exceptions, and cross-Rule
  relationships in the current repository.
- For a shared Rule, exercise representative contexts with project-local precedence and supported
  overrides.
- For a generation contract, produce and review at least one complete representative target Rule;
  use materially different targets when claiming broad portability.

## Review the Rule

In the shared independent-review step, try to falsify the complete Rule against these checks:

- Reconstruct the class, owner, strength, scope, applicability, precedence, exceptions, boundaries,
  and outcome as a field-to-value-to-evidence matrix. Fail any implicit value or unsupported claim
  of inapplicability.
- Build a condition-to-outcome matrix for every threshold, boundary, overlap, range, and exclusion.
  Test the nearest false positive and false negative for each row, and fail any undefined label or
  predicate that could change the result.
- Walk representative broader-Rule, more-specific-Rule, precedence, and exception combinations.
  Fail any case that produces two outcomes, no outcome, or an unstated override.
- Check that the Rule states policy rather than requiring an invented execution sequence. For a
  generation contract, separately check the complete generated Rule, generation evidence, Review,
  Acceptance, and handoff.
- Return `FAIL` with the exact passage, violated gate, and counterexample whenever another Agent
  could reach a different policy outcome from the same supported facts.
