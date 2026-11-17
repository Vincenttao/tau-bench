"""A2A customer-visible output extraction; protocol completion is not business success."""


def customer_reply(task):
    state = task['status']['state']
    waiting = state == 'TASK_STATE_INPUT_REQUIRED'
    if not waiting and state != 'TASK_STATE_COMPLETED':
        raise ValueError('Runtime task is neither completed nor awaiting customer input: ' + state)
    parts = task['status'].get('message', {}).get('parts', []) if waiting else [
        part for artifact in task.get('artifacts', []) for part in artifact.get('parts', [])]
    content = '\n'.join(part['text'] for part in parts if isinstance(part.get('text'), str)).strip()
    if not content:
        raise ValueError('Runtime returned no customer-visible output')
    return {'type': 'content', 'content': content, 'waiting': waiting,
            'runtime_task_id': task['id'], 'runtime_task_state': state}
