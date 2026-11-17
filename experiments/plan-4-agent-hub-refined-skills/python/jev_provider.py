"""Native TypeSafe HTTP probe adapter; NOT a Hub authorization provider.

No SDK retries, redirects, generated rationales, or inferred evidence citations.
Question wording and provisional thresholds are versioned here for audit.
"""
import json
import math
import urllib.request
from urllib.error import HTTPError, URLError

MODEL = 'jev-1.14.0'
ENDPOINT = 'https://api.typesafe.ai/v1'
QUESTION_VERSION = 'claim-evidence-probe'
LOW, HIGH = 0.3, 0.7  # Provisional probe thresholds, not bank-write authorization.


class JevError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class JevClient:
    def __init__(self, key, timeout=60, *, long_context=False):
        if not key or any(c in key for c in '\r\n'):
            raise ValueError('Missing or invalid TypeSafe credential')
        self._key = key
        self.timeout = timeout
        self.long_context = long_context
        self.opener = urllib.request.build_opener(NoRedirect())

    def _request(self, path, payload=None):
        headers = {'Authorization': 'Bearer ' + self._key, 'Accept': 'application/json'}
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            if payload.get('assets') or any(q.get('type') == 'box' for q in payload.get('questions', {}).values()):
                headers['TypeSafe-Danger-Zone-Images'] = 'true'
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode()
        if self.long_context and data is not None and len(data) >= 65_536:
            headers['TypeSafe-Danger-Zone-Long-Context'] = 'true'
        request = urllib.request.Request(ENDPOINT + path,
                data=data, headers=headers)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                result = json.loads(response.read())
        except HTTPError as error:
            raise JevError(f'TypeSafe HTTP {error.code}; no automatic retry') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise JevError('TypeSafe transport or JSON error; result unknown; no retry') from None
        if not isinstance(result, dict):
            raise JevError('Invalid response object')
        return result

    def models(self):
        return self._request('/models')

    def ask(self, request):
        result = self._request('/systemone', request)
        if not isinstance(result.get('answers'), dict) or not isinstance(result.get('model'), str):
            raise JevError('Missing typed answers or actual model identity')
        usage = result.get('usage', {})
        if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise JevError('Missing or invalid token accounting')
        return result


def claim_request(evidence, claim):
    return {'model': MODEL, 'state': {'evidence': evidence, 'claim': claim}, 'questions': {
        'evidence_present': {'type': 'noul', 'instructions': 'Does `evidence` contain information about the subject of `claim`?'},
        'supported': {'type': 'noul', 'instructions': 'Is `claim` supported by `evidence`?'}
    }}


def probability(response, name):
    answer = response.get('answers', {}).get(name, {})
    value = answer.get('noul')
    if answer.get('type') != 'noul' or type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise JevError('Invalid Noul answer: ' + name)
    return value


def interpret_claim(response):
    present, supported = probability(response, 'evidence_present'), probability(response, 'supported')
    if present <= HIGH:
        return 'unknown'
    return 'supported' if supported > HIGH else 'unsupported' if supported < LOW else 'unknown'


def visible_box(response):
    if probability(response, 'present') <= HIGH:
        return None
    answer = response.get('answers', {}).get('target', {})
    box = answer.get('box', {})
    if answer.get('type') != 'box' or any(type(box.get(k)) not in (int, float) or not math.isfinite(box[k]) or not 0 <= box[k] <= 1 for k in ('left', 'right', 'top', 'bottom')):
        raise JevError('Invalid Box answer')
    if box['left'] >= box['right'] or box['top'] >= box['bottom']:
        raise JevError('Invalid Box ordering')
    return box
