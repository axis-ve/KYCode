import search
import store
import text


def save_note(title, body):
    note = {"title": text.clean_title(title), "body": body}
    note_id = store.put(note)
    search.index(note_id, note)
    return note_id


def get_note(note_id):
    return store.get(note_id)
