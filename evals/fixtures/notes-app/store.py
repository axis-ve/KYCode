NOTES = {}


def put(note):
    note_id = len(NOTES) + 1
    NOTES[note_id] = note
    return note_id


def get(note_id):
    return NOTES[note_id]
