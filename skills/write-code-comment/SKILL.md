---
name: write-code-comment
description: Use when adding, editing, or reviewing code comments or documentation comments so they follow the target project's conventions and explain non-obvious intent, constraints, or behavior.
---

# Write Code Comment

This Judgment-led Skill writes a comment only when project convention requires it or it preserves
information that the code, name, signature, type, and immediate control flow do not already express.

## Judgment Frame

Judge the comment from the request, relevant code, applicable repository and language rules, nearby
maintained comments, formatter or linter configuration, and generated-file ownership. Let the
target project decide:

- comment language and terminology;
- line, block, and documentation-comment syntax;
- punctuation, capitalization, wrapping, and tag conventions;
- whether a declaration should use a doc comment, docstring, annotation, or no comment;
- required markers such as `TODO`, suppression directives, or API documentation tags.

Project conventions override the defaults below. Stop before modifying a generated target whose
source owner or permitted edit surface cannot be established.

Identify what a future reader would otherwise misunderstand, violate, or have to rediscover. Useful
comment roles include:

- behavior that callers cannot infer from the signature;
- invariants and ordering constraints;
- lifecycle, ownership, cancellation, or concurrency requirements;
- edge cases, fallback behavior, and expected failure modes;
- rationale for a non-obvious choice or for rejecting an obvious alternative;
- external protocol, compatibility, security, or product requirements.

If naming or structure is the real problem, report it without changing it unless that work is also
authorized.

## Write with restraint

For an authorized edit, supply the missing information in the smallest statement, using the target
language's syntax and project tone without narrating the next line.

When the project is silent:

- Match the language and terminology of nearby maintained documentation.
- Use the language-native documentation form for public declarations and a normal line or block
  comment for local reasoning.
- Prefer active, direct prose and one idea per comment.
- Use a complete sentence for prose comments; keep markers, directives, code fragments, and URLs in
  their required native form.
- Refer to parameters, exceptions, and symbols with the documentation syntax supported by the
  target language.

Preserve valid markers, suppression directives, documentation tags, URLs, code fragments, and
generated comments in their required form. Change one only when the target project's rule or the
request requires it.

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

## Validate and report

For review-only work, make no file or structural change and run only read-only checks. Report
actionable missing, misleading, redundant, or stale comments by location, or report that no
actionable issue was found.

For edits, run every declared relevant formatter, documentation check, analyzer, or linter and
report where comments were added, changed, or deliberately omitted and what information they
preserve. If no relevant check is declared, label the result untested. If a required check is
unavailable or fails, report it and do not claim successful completion.

In both branches, name every check and distinguish validated, untested, and failed outcomes.
