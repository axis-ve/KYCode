# Examples

Patterns for [SKILL.md](SKILL.md). These examples are illustrative, not reports of inspected user code or completed voice tests.

## Voice walkthrough and interruption

Prompt: "Talk me through borrowing two copies of the atlas, then trying another two. Don't change any files."

After inspecting the reading-room fixture, a suitable spoken section is: "The library starts with three copies. The borrowing function checks whether there are enough before changing the count. Your first request takes two, so one is left."

User: "Wait, does that get saved if I restart?"

Response: "In this example, the count lives in memory. I don't see a write to a file or database. Restarting this script recreates the original count. Back to your second request: it asks for two when only one remains, so it's rejected and that last copy stays available."

Companion text identifies `library.py`, `borrow`, and `BOOKS`, with a runnable check for the return values and remaining count. Describe a check as executed only after running it.

Bad: reading a file listing aloud, delivering the entire codebase as a monologue, ignoring the detour, or restarting the explanation afterward.

## Signpost and bookmark

Opening a spoken walkthrough: "Three steps: the button, the check on how many copies are left, and the count it changes. Starting with the button."

On a detour: "We're at step two of three, the check on copies left. Your question first: ..." The return bridge then picks up at step two.

Bad: launching into the first function with no sense of how long the path is, or answering a detour and then restarting from the button.

## Reach check before a shared fix

Prompt: "When I press Save, a note titled My Plans comes back as my plans. Fix it so titles keep their capitals."

Good, in the notes-app fixture: follows Save to `clean_title`, then searches for its other callers before editing and finds `search.py` and `export.py`. It changes only how Save stores the title, so search stays case-insensitive and exports keep the `my-plans.md` filename. Spoken: "Two other features use the same cleanup, search and export, so I changed only what Save stores."

Bad: removes the lowercasing from `clean_title`. Save looks fixed, but searching for "plans" stops finding the note and exported files change name.

## Text-only request

Prompt: "Text only, please. Give me the path and a command to check it."

Good: provide the compact written trace and runnable check without asking the user to enable voice. Voice is the primary experience, while the user's chosen medium controls this response.

## Written companion for a feature trace

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
