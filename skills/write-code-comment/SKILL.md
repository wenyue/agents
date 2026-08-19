---
name: write-code-comment
description: Use when adding, editing, or reviewing code comments or documentation comments so they follow the target project's conventions and explain non-obvious intent, constraints, or behavior.
---

# Write Code Comment

Unless a project convention requires a comment, write one only when it carries information that the
code, name, signature, type, or immediate control flow does not already express.

## Read Project Conventions

Before writing, read the applicable repository and language rules, nearby comments, formatter or
linter configuration, and generated-file ownership. Let the target project decide:

- comment language and terminology;
- line, block, and documentation-comment syntax;
- punctuation, capitalization, wrapping, and tag conventions;
- whether a declaration should use a doc comment, docstring, annotation, or no comment;
- required markers such as `TODO`, suppression directives, or API documentation tags.

Project conventions override the non-obviousness heuristic and the defaults below. If a target
appears generated and its ownership or permitted edit surface cannot be established, stop before
modifying it and report the generator or owner evidence needed to continue.

## Decision Workflow

1. Determine whether the request authorizes edits or asks only for review. For review-only work,
   inspect comments and relevant code, report actionable missing, misleading, redundant, or stale
   comments, run only read-only checks, and make no file or structural change. Then report the
   review result.
2. For an authorized edit, identify what a future reader would misunderstand, violate, or have to
   rediscover without the comment.
3. If the answer is nothing and no project convention requires a comment, leave the code
   uncommented. When the real problem is naming or structure, report that issue rather than changing
   it unless the user separately authorized that work.
4. Choose the comment role: API contract, invariant, lifecycle, edge case, failure behavior,
   rationale, external requirement, or local intent.
5. Write the smallest statement that supplies the missing information.
6. Apply the target language's syntax and the project's tone and formatting rules.
7. Read the code and comment together. Remove any phrase that merely narrates the next line.
8. Run every declared relevant formatter, documentation check, analyzer, or linter. If no relevant
   check is declared, report the result as untested. If a required check is unavailable or fails,
   report the unavailable or failed check and do not claim successful completion.

## High-Value Content

- behavior that callers cannot infer from the signature;
- invariants and ordering constraints;
- lifecycle, ownership, cancellation, or concurrency requirements;
- edge cases, fallback behavior, and expected failure modes;
- rationale for a non-obvious choice or for rejecting an obvious alternative;
- external protocol, compatibility, security, or product requirements.

## Defaults When the Project Is Silent

- Match the language and terminology of nearby maintained documentation.
- Use the language-native documentation form for public declarations and a normal line or block
  comment for local reasoning.
- Prefer active, direct prose and one idea per comment.
- Use a complete sentence for prose comments; keep markers, directives, code fragments, and URLs in
  their required native form.
- Refer to parameters, exceptions, and symbols with the documentation syntax supported by the
  target language.

## Examples

**Preferred**

```text
// Keep the old token until persistence succeeds so a failed write can be retried.
# The service reports healthy before the index is ready; poll the readiness endpoint instead.
```

**Avoid**

```text
// Increment the retry count.
# Return the cached value.
```

## Preserve Special Forms

Preserve valid markers, suppression directives, documentation tags, URLs, code fragments, and
generated comments in their required form. Change one only when the target project's rule or the
user's request requires it.

## Result

For review-only work, report findings and omissions by location, or report that no actionable issue
was found, together with every read-only check run or unavailable. For edits, report where comments
were added, changed, or deliberately omitted and what information they preserve. In both branches,
name each check and its result; distinguish validated, untested, and failed outcomes explicitly.
