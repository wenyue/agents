# ARB Guidelines

Strength: `Mandatory`

Scope: ARB source ownership, localization key grammar, metadata, ordering, and generation rules.

## Source Files

- Use the configured Flutter `gen-l10n` template ARB as the source of truth for keys and metadata.
- Follow the application's locale-resolution and fallback configuration when a translation is
  missing; do not assume a specific fallback ARB.
- Add a matching `@key` metadata entry for every source key.
- Use the repository-owned localization workflow to order keys when one exists; otherwise keep each
  key and its adjacent `@key` metadata entry in alphabetical order.
- Do not edit generated localization output.

## Key Grammar

Use `${module}_${filename?}_${name}{index?}`.

## Key Components

- Derive `module` from the owning application module unless project configuration declares a shared
  module.
- Use lower camel case for components and derive an optional filename component from the owning Dart
  file.
- Append digits only for repeated nearby strings with the same purpose.

## Metadata Contract

- Write metadata descriptions in English using `[Module] > Location > purpose. ~min–max chars.`.
- Render `Module` in PascalCase. Convert the owning Dart filename into one readable page or
  component name for `Location`, and use a concrete role such as `button`, `label`, `tooltip`,
  `error`, `success`, `title`, or `description` for `purpose`.
- Infer `~min–max chars.` bounds from the widget layout at the call site, not from the current string
  length. Count Latin characters as 1 and CJK characters as 2.
- Document every placeholder with its type and a representative example.

For example:

```json
{
  "album_itemCount": "{count} albums",
  "@album_itemCount": {
    "description": "[Album] > Album Page > label. ~4–12 chars.",
    "placeholders": {
      "count": {
        "type": "int",
        "example": "5"
      }
    }
  }
}
```
