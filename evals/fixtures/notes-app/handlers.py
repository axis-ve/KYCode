import export
import notes
import search


def on_save(title, body=""):
    return notes.save_note(title, body)


def on_search(query):
    return [note["title"] for note in search.find(query)]


def on_export(note_id):
    return export.export_note(notes.get_note(note_id))
