import text


def export_note(note):
    name = text.clean_title(note["title"]).replace(" ", "-") + ".md"
    return name, f"# {note['title']}\n\n{note['body']}\n"
