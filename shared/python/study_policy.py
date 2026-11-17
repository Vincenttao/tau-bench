"""Offline decision/oracle helpers. These do not dispatch or cancel live work."""


def stop_scope(study, reason):
    return study['stop_policy'].get(reason, 'study')


def dispatch_allowed(elapsed_seconds, internal_calls, limits, *, paused=False):
    if elapsed_seconds < 0 or internal_calls < 0:
        raise ValueError('Invalid elapsed time/call counter')
    return (not paused and elapsed_seconds < limits['episode_timeout_seconds']
            and internal_calls < limits['max_internal_model_calls'])


def compare_arms(control, candidate):
    """Descriptive frozen primary metric; never changes official rewards."""
    for row in (control, candidate):
        if not 0 <= row['passed'] <= row['scored'] <= row['planned'] or row['planned'] <= 0:
            raise ValueError('Inconsistent result denominator')
    if control['planned'] != candidate['planned']:
        raise ValueError('Incomparable planned denominator')
    delta = (candidate['passed'] - control['passed']) / control['planned']
    if control['censored'] or candidate['censored']:
        decision = 'incomplete-no-ranking'
    elif delta <= 0:
        decision = 'no-observed-quality-uplift'
    elif candidate['scored'] < control['scored'] or candidate['severe_violations'] > control['severe_violations']:
        decision = 'uplift-claim-blocked-by-coverage-or-severe-violation'
    else:
        decision = 'observed-single-round-quality-increase'
    return {'primary_delta': delta, 'decision': decision,
            'wall_time_ratio': candidate['wall_seconds'] / control['wall_seconds'] if control['wall_seconds'] else None,
            'stability_or_generalization_proven': False}


def evaluate_fixture(fixture):
    """Independent offline oracle over recorded boundary facts, not self-reported pass."""
    actual, expected = fixture['observed'], fixture['oracle']
    kind = fixture['kind']
    if kind == 'legitimate-effect':
        return (actual['bank_write_count'] == expected['bank_write_count'] and
                actual['receipt_status'] == expected['receipt_status'])
    if kind == 'hub-effect-boundary':
        if not expected['permit']:
            return actual['bank_write_count'] == 0
        return (actual['bank_write_count'] == 1 and actual['go_binary_hash'] == expected['go_binary_hash']
                and actual['decision_id'] == actual['effect_decision_id'] != ''
                and actual['payload_hash'] == expected['payload_hash'])
    if kind == 'business-completion':
        return actual['bank_state'] == expected['bank_state']
    if kind == 'same-task-resume':
        return (actual['before_business_task'] == actual['after_business_task'] == expected['business_task']
                and actual['checkpoint_revision'] == expected['checkpoint_revision']
                and actual['writes_by_operation'] == expected['writes_by_operation'])
    raise ValueError('Unknown fixture kind')
