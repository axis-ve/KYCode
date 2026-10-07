import sqlite3


class SaveConflict(Exception):
    pass


class Repository:
    def __init__(self, path, guard_revision=False):
        self.path = str(path)
        self.guard_revision = guard_revision
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, body TEXT, revision INTEGER)')
            db.execute("INSERT OR IGNORE INTO documents VALUES (1, 'Starting text', 0)")

    def read(self, document_id):
        with sqlite3.connect(self.path) as db:
            row = db.execute('SELECT body, revision FROM documents WHERE id = ?', (document_id,)).fetchone()
        return {'id': document_id, 'body': row[0], 'revision': row[1]}

    def write(self, document_id, body, expected_revision):
        with sqlite3.connect(self.path) as db:
            if self.guard_revision:
                result = db.execute(
                    'UPDATE documents SET body = ?, revision = revision + 1 WHERE id = ? AND revision = ?',
                    (body, document_id, expected_revision),
                )
                if result.rowcount != 1:
                    raise SaveConflict('The document changed after this draft was loaded.')
            else:
                db.execute(
                    'UPDATE documents SET body = ?, revision = revision + 1 WHERE id = ?',
                    (body, document_id),
                )
            row = db.execute('SELECT body, revision FROM documents WHERE id = ?', (document_id,)).fetchone()
        return {'id': document_id, 'body': row[0], 'revision': row[1]}
