# Rule

A Rule owns one persistent policy. For an Ordinary Artifact, this reference applies to the
candidate itself. For a Generation Contract, it defines the semantics the guidance must establish
for the future target.

## Establish the policy

Resolve the Rule's class, owner, policy, strength, scope, applicability, precedence, exceptions,
boundaries, and outcomes from accepted intent, the active Rule schema, and governing evidence.
Every applicable field needs one supported value; omit a field only when evidence proves that it
cannot change the policy.

For a Generation Contract, require the guidance to identify the evidence that selects every
applicable target field and to stop when the evidence still permits materially different policies.
Do not invent target policy merely to make the contract appear complete.

## Write one policy

- Lead with the governing policy. Co-locate each predicate with its required outcome and exception.
- Keep every requirement in the narrowest Rule that owns it; do not duplicate or silently override
  a more-specific Rule.
- Use observable predicates and outcomes. For each threshold, overlap, range, exception, and
  exclusion, reject its nearest false positive and false negative without relying on an undefined
  label.
- Keep ordered execution procedure in a Skill. Use order in Rule-generation guidance only when it
  changes the authored result.
- Use headings for stable policy regions or real applicability branches, lists for peer
  requirements, and tables only for exact mappings or repeated-field comparisons.

## Review and accept Rule semantics

Semantic Review reconstructs every applicable field and condition-to-outcome mapping from the
candidate and evidence. Fail an implicit field, unsupported inapplicability, invented predicate,
duplicated owner, unstated override, or case where the same facts produce two outcomes or no
outcome.

Select only the highest-risk relevant cases:

- an included or applicable case and its nearest excluded or inapplicable case;
- an affected threshold, range, overlap, exception, or owner boundary; and
- a precedence or conflict combination when another Rule can change the result.

With `ordinary-artifact.md`, apply these cases to the candidate's real policy seam. With
`generation-contract.md`, statically verify that the guidance obtains the required evidence and
chooses one action or stop for the same input classes. Do not create a target for contract
Acceptance.
