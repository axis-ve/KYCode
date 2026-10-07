class DocumentService:
    def __init__(self, repository):
        self.repository = repository

    def save(self, payload):
        return self.repository.write(payload['id'], payload['body'], payload['revision'])
