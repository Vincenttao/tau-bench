"""Bind presentation-only Markdown differences to a literal current-message span.

No word, amount, whitespace, case or punctuation normalization is permitted.
Unmatched or ambiguous text stays unchanged and fails normal quote validation.
"""
import copy
import re

MARKUP = re.compile(r'(?<!\w)(\*\*|__)(?=\S)(.*?\S)\1(?!\w)')


def visible_map(text):
    omitted = set()
    for match in MARKUP.finditer(text):
        width = len(match.group(1))
        omitted.update(range(match.start(), match.start()+width))
        omitted.update(range(match.end()-width, match.end()))
    positions = [i for i in range(len(text)) if i not in omitted]
    return ''.join(text[i] for i in positions), positions


def bind_quote(content, quote):
    if not isinstance(quote, str) or not quote or quote in content: return quote
    visible, positions = visible_map(content)
    target, _ = visible_map(quote)
    if not target: return quote
    start = visible.find(target)
    if start < 0 or visible.find(target, start+1) >= 0: return quote
    return content[positions[start]:positions[start+len(target)-1]+1]


def bind_proposal(content, proposal):
    bound = copy.deepcopy(proposal)
    for field in ('goals', 'existing_routes'):
        for item in bound.get(field, []):
            if 'quote' in item: item['quote'] = bind_quote(content, item['quote'])
    if 'context_quote' in bound: bound['context_quote'] = bind_quote(content, bound['context_quote'])
    return bound
