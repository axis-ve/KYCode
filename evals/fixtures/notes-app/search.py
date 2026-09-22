import store
import text

INDEX = {}


def index(note_id, note):
    for word in text.clean_title(note["title"]).split():
        INDEX.setdefault(word, set()).add(note_id)


def find(query):
    ids = None
    for word in text.clean_title(query).split():
        matches = INDEX.get(word, set())
        ids = matches if ids is None else ids & matches
    return [store.get(note_id) for note_id in sorted(ids or ())]
