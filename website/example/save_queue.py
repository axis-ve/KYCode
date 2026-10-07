class SaveQueue:
    def __init__(self, api):
        self.api = api
        self.pending = []

    def enqueue(self, snapshot):
        self.pending.append(dict(snapshot))

    def flush_one(self):
        return self.api.save_document(self.pending.pop(0))
