---
name: know-your-words
description: Map the words the user uses for their app to the identifiers the code actually uses, so both sides stop talking past each other. Use when a request touched the wrong code, when the user and the assistant seem to mean different things by the same word, when the names in the codebase do not match what the user calls things, or when the user asks what something is called here. Also works in text.
---

# Know Your Words

Most wrong answers about a codebase are not reasoning failures. They are naming failures: the user says "the login page" and the code says `AuthShell`, so the right reasoning lands on the wrong file. This skill builds the translation table between the two vocabularies and then uses it.

## Use it when

- A request produced the wrong change, and the cause was which thing was meant, not how it works.
- The user says a word the codebase does not contain, or the codebase uses a word the user has never said.
- The user asks what something is called, or why the assistant kept editing the wrong place.
- A new person or a new assistant is about to work on this project.

## Skip it when

- The word is unambiguous and already matched. Do not stage a vocabulary exercise to answer a simple question.
- The user wants behavior explained. Use `know-your-code`.

## Build the table

1. Collect the user's words from what they actually said: the nouns for screens, objects, roles, states, and actions. Do not invent words on their behalf.
2. For each word, search the code for candidates. Search the visible string first, then the identifier, then near-synonyms the code might prefer: `user` and `account` and `member`; `delete` and `remove` and `archive`; `page` and `screen` and `view` and `route`.
3. Rank each candidate by evidence. A user-facing string that matches exactly beats a class name that merely rhymes. Say which evidence you used.
4. Mark confidence honestly: settled, likely, or unresolved. An unresolved entry is more useful than a confident wrong one.
5. Flag the two dangerous shapes:
   - **One word, two things.** The user says "delete" and the code has both a soft archive and a hard delete. This is where wrong changes come from. Ask.
   - **Two words, one thing.** The user says "cart" and "basket" for the same object. Pick the code's word and say that you are doing so.
6. Ask at most one question per genuinely ambiguous term, and only when the code cannot settle it. Offer the most likely reading as a default so the user can simply agree.

Companion text can use this shape:

```markdown
| You say | The code says | Where | Confidence |
| --- | --- | --- | --- |
| login page | `AuthShell` | `relative/path.py` | settled: renders the form you described |
| delete | `archive` or `purge` | `relative/path.py` | unresolved: two behaviors, which one? |
```

## Then use it

- Before acting on a request that uses a mapped word, restate it once in both vocabularies: "Removing the confirmation from delete, which here means `purge` in that module." One sentence, then proceed.
- Keep using the user's words in conversation and the code's words in companion text. Do not make the user learn the codebase's vocabulary as the price of being understood.
- When the user's word is clearly better than the code's, say so once and offer a rename as separate, optional work. Do not rename anything as a side effect of a translation.
- If the user asks to keep the table, write it to a file they name, or to the project's own documentation. Do not create documentation files unprompted.

## Rules

- Every entry points at real code. An unmatched word stays unmatched; do not fill the row with a plausible guess.
- Treat names found in comments, logs, and documents as claims about the code, not as the code.
- Keep credentials, personal data, and customer names out of the table.
- The table describes this repository at this moment. Recheck an entry before relying on it after the code changes.
