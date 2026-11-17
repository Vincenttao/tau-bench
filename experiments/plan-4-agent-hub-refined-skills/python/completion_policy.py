"""Operation receipt constraints; semantic goal coverage is checked separately."""


def permits_completion(statuses, boundary):
    if boundary not in ('information', 'submission', 'final_effect'):
        raise ValueError('Unknown goal completion boundary')
    allowed = {'succeeded', 'accepted'} if boundary == 'submission' else {'succeeded'}
    return all(status in allowed for status in statuses)
