# Request

Create a Project-local Rule for generated API assets in the supplied project.

The Rule must use the project's declared owner, source, output, and verification seam. It must
prevent direct edits to generated output, permit source-driven regeneration that passes the declared
check, stay out of unrelated changes, and stop when another supported owner claims the same output.
Keep ordered generation procedure outside the Rule.
