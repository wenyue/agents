---
name: write-comment
description: Use when adding, editing, or reviewing code comments or documentation comments so they follow the target project's conventions and explain non-obvious intent, constraints, or behavior.
---

# Write Comment

Write a comment only when it carries information that the code, name, signature, type, or immediate
control flow does not already express.

## Read Project Conventions

Before writing, read the applicable repository and language rules, nearby comments, formatter or
linter configuration, and generated-file ownership. Let the target project decide:

- comment language and terminology;
- line, block, and documentation-comment syntax;
- punctuation, capitalization, wrapping, and tag conventions;
- whether a declaration should use a doc comment, docstring, annotation, or no comment;
- required markers such as `TODO`, suppression directives, or API documentation tags.

Project conventions override the defaults below.

## Decision Workflow

1. Identify what a future reader would misunderstand, violate, or have to rediscover without the
   comment.
2. If the answer is nothing, do not add a comment; improve the name or structure when that is the
   real problem.
3. Choose the comment role: API contract, invariant, lifecycle, edge case, failure behavior,
   rationale, external requirement, or local intent.
4. Write the smallest statement that supplies the missing information.
5. Apply the target language's syntax and the project's tone and formatting rules.
6. Read the code and comment together. Remove any phrase that merely narrates the next line.
7. Run the project's relevant formatter, documentation check, analyzer, or linter.

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

Good comments add a missing constraint or reason:

```text
// Keep the old token until persistence succeeds so a failed write can be retried.
# The service reports healthy before the index is ready; poll the readiness endpoint instead.
```

Bad comments restate visible code:

```text
// Increment the retry count.
# Return the cached value.
```

## Preserve Special Forms

Do not rewrite a valid marker, suppression directive, documentation tag, URL, code fragment, or
generated comment merely to make it sentence-shaped. Change it only when the target project's rule
or the user's request requires the change.

## Result

Report where comments were added, changed, or deliberately omitted, what non-obvious information
they preserve, and which project check validated them.
