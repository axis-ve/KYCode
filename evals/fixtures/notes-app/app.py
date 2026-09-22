import handlers

BUTTONS = {
    "Save": handlers.on_save,
    "Search": handlers.on_search,
    "Export": handlers.on_export,
}


def press(label, **fields):
    return BUTTONS[label](**fields)
