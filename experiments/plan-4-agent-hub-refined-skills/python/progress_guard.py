"""Persistent correction bound for the same goals and visible evidence."""
import json
from pathlib import Path
import threading

from task_session import durable_json


class ProgressGuard:
    def __init__(self, path, limit):
        if type(limit) is not int or limit < 1: raise ValueError('Positive correction limit required')
        self.path, self.limit, self.lock = Path(path), limit, threading.Lock()
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {'version': 1, 'counts': {}}
        if (set(self.state) != {'version', 'counts'} or self.state['version'] != 1
                or not isinstance(self.state['counts'], dict)
                or any(not isinstance(key, str) or type(value) is not int or not 0 <= value <= limit
                       for key, value in self.state['counts'].items())):
            raise ValueError('Invalid persistent correction state; progression refused')

    def reserve(self, context):
        if not isinstance(context, str) or not context: raise ValueError('Correction context required')
        with self.lock:
            count = self.state['counts'].get(context, 0)
            if count >= self.limit: return False
            next_state = {'version': 1, 'counts': {**self.state['counts'], context: count+1}}
            durable_json(self.path, next_state)
            self.state = next_state
            return True
