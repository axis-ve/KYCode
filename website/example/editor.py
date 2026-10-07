class Editor:
    def __init__(self, document, api, queue):
        self.document_id = document['id']
        self.body = document['body']
        self.revision = document['revision']
        self.api = api
        self.queue = queue
        self.message = ''

    def snapshot(self):
        return {'id': self.document_id, 'body': self.body, 'revision': self.revision}

    def schedule_autosave(self):
        self.queue.enqueue(self.snapshot())

    def save_now(self):
        result = self.api.save_document(self.snapshot())
        if result['status'] == 200:
            self.revision = result['document']['revision']
            self.message = 'Saved'
        else:
            self.message = 'The document changed. Your draft is still here; compare it before saving again.'
        return result
