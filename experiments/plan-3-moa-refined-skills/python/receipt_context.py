"""Episode-local projection of observed write requests and their official replies."""
import json
import threading


class ReceiptContext:
    def __init__(self, directory):
        self.path = directory / 'operation-receipts.json'
        self.entries = {}
        self.lock = threading.Lock()

    def refused(self, call_id, actor, operation, owners):
        with self.lock:
            self.entries[call_id] = {'actor': actor, 'operation': operation,
                                     'state': 'refused before submission', 'authorized_domains': owners}
            self._publish()

    def start(self, call_id, actor, operation):
        with self.lock:
            if call_id in self.entries:
                raise ValueError('Duplicate operation identity')
            self.entries[call_id] = {'actor': actor, 'operation': operation,
                                     'state': 'no official reply yet'}
            self._publish()

    def reply(self, call_id, content, error):
        """Keep raw business wording distinct from the outer transport error flag."""
        with self.lock:
            entry = self.entries.get(call_id)
            if entry is None:
                return
            entry.update(state='official reply received', error=error, reply=content[:1000],
                         truncated=len(content) > 1000)
            self._publish()

    def _publish(self):
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.entries, ensure_ascii=False))
        temp.replace(self.path)
