"""Offline checker for synthetic reward reviews. All amounts and rewards are integer cents."""
from decimal import Decimal, ROUND_HALF_UP


def check_review(transactions, policies, reviewed):
    by_id = {row['id']: row for row in transactions}
    if len(by_id) != len(transactions):
        raise ValueError('Fixture transaction identities must be unique')
    seen = set()
    findings = []
    for row in reviewed:
        identity = row['id']
        if identity in seen or identity not in by_id:
            findings.append((identity, 'duplicate or unknown item'))
            continue
        seen.add(identity)
        item = by_id[identity]
        policy = policies.get(item['product'])
        if policy is None:
            if row.get('status') != 'unresolved' or row.get('difference') is not None:
                findings.append((identity, 'no applicable policy'))
            continue
        rate = policy['merchant_rates'].get(item['merchant'], policy['base_rate'])
        expected = (Decimal(item['purchase']) * Decimal(rate)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        if row.get('policy') != policy['source'] or row.get('difference') != expected - item['credited']:
            findings.append((identity, 'policy or signed difference mismatch'))
        if row.get('status') == 'submitted' and not item.get('submission_receipt'):
            findings.append((identity, 'no submission receipt'))
    return findings + [(identity, 'missing item') for identity in sorted(by_id.keys() - seen)]
