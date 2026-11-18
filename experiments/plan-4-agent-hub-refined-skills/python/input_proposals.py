"""Deterministic proposal normalization; semantic approval remains with Jev."""
import copy
from collections import defaultdict


def normalize_context_routes(content, proposal):
    routes = proposal.get('existing_routes')
    if not isinstance(routes, list) or len(routes) > 32: return proposal
    groups = defaultdict(list)
    for route in routes:
        if (not isinstance(route, dict) or not isinstance(route.get('goal_id'), str)
                or not isinstance(route.get('quote'), str)):
            return proposal
        groups[route['goal_id']].append(route)
    repeated = {goal for goal, group in groups.items() if len(group) > 1}
    if not repeated: return proposal
    for goal in repeated:
        if any(set(route) != {'goal_id', 'action', 'quote'} or route['action'] != 'context'
                or not route['quote'].strip() or route['quote'] not in content for route in groups[goal]):
            return proposal  # Never discard conflict, confirmation, malformed or fabricated evidence.
    result = copy.deepcopy(proposal); merged = []; seen = set()
    for route in result['existing_routes']:
        goal = route['goal_id']
        if goal not in repeated: merged.append(route)
        elif goal not in seen:
            merged.append({'goal_id': goal, 'action': 'context', 'quote': content})
            seen.add(goal)
    result['existing_routes'] = merged
    return result
