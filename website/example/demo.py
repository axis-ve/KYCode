"""A deliberately small editor model, not a browser app or a recorded host session."""
import json
from pathlib import Path
import tempfile
from api import DocumentAPI
from documents import DocumentService
from editor import Editor
from save_queue import SaveQueue
from storage import Repository


def setup(path, guard_revision):
    repository = Repository(path, guard_revision)
    api = DocumentAPI(DocumentService(repository))
    queue = SaveQueue(api)
    editor = Editor(repository.read(1), api, queue)
    return repository, api, queue, editor


def delayed_autosave(path, guard_revision):
    repository, api, queue, editor = setup(path, guard_revision)
    editor.body = 'Earlier draft'
    editor.schedule_autosave()
    editor.body = 'Finished paragraph'
    manual = editor.save_now()
    delayed = queue.flush_one()
    reopened = Repository(path, guard_revision).read(1)
    result = {'manual_save_status': manual['status'], 'delayed_autosave_status': delayed['status'], 'after_reopening': reopened['body']}
    assert manual['status'] == 200
    assert delayed['status'] == (409 if guard_revision else 200)
    assert reopened['body'] == ('Finished paragraph' if guard_revision else 'Earlier draft')
    return result


def independent_editors(path):
    repository, api, queue, first = setup(path, True)
    second = Editor(repository.read(1), api, SaveQueue(api))
    first.body = 'First writer'
    second.body = 'Second writer'
    assert first.save_now()['status'] == 200
    assert second.save_now()['status'] == 409
    assert repository.read(1)['body'] == 'First writer'
    assert second.body == 'Second writer'
    assert 'Your draft is still here' in second.message
    current = repository.read(1)
    second.revision = current['revision']  # Simulate an explicit choice after reviewing the current text.
    assert second.save_now()['status'] == 200
    assert Repository(path, True).read(1)['body'] == 'Second writer'
    return {'conflicting_draft_retained': True, 'save_after_review': 'Second writer'}


def autosave_arrives_first(path):
    repository, api, queue, editor = setup(path, True)
    editor.body = 'Earlier draft'
    editor.schedule_autosave()
    editor.body = 'Finished paragraph'
    assert queue.flush_one()['status'] == 200
    assert editor.save_now()['status'] == 409
    assert editor.body == 'Finished paragraph'
    assert repository.read(1)['body'] == 'Earlier draft'
    return {'manual_save_status': 409, 'unsaved_local_draft': editor.body, 'stored_text': repository.read(1)['body']}


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='kycode-editor-check-') as directory:
        root = Path(directory)
        results = {
            'before': delayed_autosave(root / 'before.db', False),
            'after': delayed_autosave(root / 'after.db', True),
            'two_editors': independent_editors(root / 'two.db'),
            'reverse_order': autosave_arrives_first(root / 'reverse.db'),
        }
        print(json.dumps(results, indent=2))
        print('All four scenarios passed.')
