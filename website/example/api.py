from storage import SaveConflict


class DocumentAPI:
    def __init__(self, service):
        self.service = service

    def save_document(self, payload):
        try:
            return {'status': 200, 'document': self.service.save(payload)}
        except SaveConflict as error:
            return {'status': 409, 'message': str(error)}
