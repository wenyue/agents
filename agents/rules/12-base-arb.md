# ARB Guidelines

Strength: `Mandatory`

Scope: ARB source ownership, localization key grammar, metadata, ordering, and generation rules.

## Source Files

- Use `zh.arb` as the Flutter `gen-l10n` template and the source of truth for keys and metadata.
- Use `en.arb` as the runtime fallback when a translation is missing.
- Add a matching `@key` metadata entry for every key in `zh.arb`.
- Sort all keys alphabetically within each ARB file.

## Key Grammar

Use this key shape:

```text
${module}_${filename?}_${name}{index?}
```

```text
GOOD: album_title, album_detailBase_button, global_cancelButton, album_tip2
BAD:  title, Album_Title, _album_title, album_detail_base_button
```

## Key Components

- `module` is required and uses lower camel case. For keys used by Dart files, derive it from the
  first directory under `lib/` and convert snake case to lower camel case. Configure shared
  cross-module key modules in the target project's analyzer, lint, or localization configuration.
- `filename` is optional. Convert the Dart filename stem to camel case, such as `detail_base` to
  `detailBase`.
- `name` is required and uses camel case to state the purpose, such as `title`, `button`, `tip`,
  `error`, or `success`.
- `index` is optional. Append digits to `name` for repeated nearby strings that share one purpose.

## Metadata Contract

Use this metadata shape:

```json
"album_title": "专辑标题",
"@album_title": {
  "description": "[Album] > Album Page > title. ~4–12 chars.",
  "placeholders": { "count": { "type": "int", "example": "5" } }
}
```

- Write metadata in English. Only translation values use the target locale language.
- Capitalize the module in brackets, such as `[Album]` or `[Filter]`.
- Use one readable filename level for the location, such as `albumDetailBase` to
  `Album Detail Page`.
- State the purpose as button, label, tooltip, error, success, title, or description.
- Infer `~min–max chars.` bounds from the widget layout at the call site, not from the current string
  length. Count Latin characters as 1 and CJK characters as 2.
- Document every placeholder.

## Prohibited Forms

- Do not omit matching `@key` metadata.
- Do not use a metadata description outside the `[Module] > ...` shape.
- Do not estimate character bounds from the current string length.
- Do not use keys without a module prefix or with inconsistent casing.
- Do not write metadata in a language other than English.
