Saved text reverts example

A constructed Python model of an editor, manual saves, queued autosaves,
an API boundary, and a real SQLite store. It has no browser UI or HTTP server.
It demonstrates application behavior, not a completed AI host evaluation.

Python 3.9 or newer. No dependencies. Extract the ZIP, then run:

python3 -B demo.py

The demo checks the original overwrite, a revision-checked fix,
two conflicting editors, and the reverse arrival order. It also checks
that a reviewed retry can save and stored data survives reopening.
The demo uses temporary databases and removes them afterward.
