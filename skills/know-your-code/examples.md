# Examples

Patterns for [SKILL.md](SKILL.md). Match the shape, not the domain.

## Feature trace

Prompt:

```text
What happens when I press Save? Follow it from the button to storage. Do not change any files.
```

Good answer shape:

```markdown
## Path
Save button -> `handle_save` -> `write_document` -> documents table

## Stored data
One row per document with title, body, and updated timestamp.

## Files
- `project/src/editor.py`: wires the Save button to `handle_save`
- `project/src/storage.py`: `write_document` persists the row

## Check
Run the app, press Save, and read back the row with the project's own show command.
```

Bad: generic architecture, no handler name, no stored shape, no check.

## Bug diagnosis

Prompt:

```text
A small parcel displays $4.50 but the quote asks for $450. Find the cause and show how to reproduce it before proposing a fix.
```

Good: names the extra unit conversion in `quote`, keeps the correct `label` function unchanged, and gives exact inputs with expected outputs such as one small parcel at 450 cents.

Bad: repeats the user's guessed cause without reading `quote`, or rewrites both functions.

## Scope

Prompt asks for an explanation with no file changes. Good: source files stay unchanged. Prompt asks for a bounded fix. Good: only the affected behavior changes, with a check on the real path.
