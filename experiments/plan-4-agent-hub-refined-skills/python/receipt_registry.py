"""Pinned control contracts and conservative typed interpretation of bank receipts."""
from business_judgment import parse_credit_dispute_receipt


class ReceiptInterpreter:
    def __init__(self, judgments): self.judgments = judgments

    def parse(self, tool, arguments, content, error, *, now):
        if error or not isinstance(content, str): return {'status': 'unknown'}
        if content.startswith('Error:'): return {'status': 'rejected'}
        if tool == 'file_credit_card_transaction_dispute_4829': return parse_credit_dispute_receipt(content)
        if tool == 'unlock_discoverable_agent_tool':
            expected = arguments.get('agent_tool_name')
            return {'status': 'succeeded' if expected and content.startswith('Tool unlocked: '+expected+'\n') else 'unknown'}
        if tool == 'give_discoverable_user_tool':
            expected = arguments.get('discoverable_tool_name')
            return {'status': 'succeeded' if expected and content.startswith('Tool given to user: '+expected+'\n') else 'unknown'}
        if tool == 'transfer_to_human_agents':
            return {'status': 'accepted' if content.startswith('Transfer successful (reason: ') else 'unknown',
                    'meaning': 'handoff accepted; human resolution is not established'}
        if self.judgments is None: return {'status': 'unknown'}
        questions = {
            'accepted': {'type': 'noul', 'instructions': 'Does the receipt establish only submission or receipt of a request for future approval or processing?'},
            'pending': {'type': 'noul', 'instructions': 'Does the receipt say the operation outcome is still pending or not yet decided?'},
            'succeeded': {'type': 'noul', 'instructions': 'Does this receipt explicitly confirm that the state change requested by this exact tool invocation has completed, rather than merely receiving an application?'},
            'rejected': {'type': 'noul', 'instructions': 'Does the receipt explicitly reject or report failure of the requested operation?'}}
        try:
            values, reference = self.judgments.ask({'tool': tool, 'arguments': arguments, 'official_receipt': content}, questions, now=now)
        except Exception as error:
            return {'status': 'unknown', 'provider_error': type(error).__name__}
        low, high = self.judgments.policy.low, self.judgments.policy.high
        if any(low <= value <= high for value in values.values()): return {'status': 'unknown', 'observation_ref': reference}
        positive = {key for key, value in values.items() if value > high}
        if positive <= {'accepted', 'pending'} and positive:
            status = 'accepted' if 'accepted' in positive else 'pending'
        elif positive == {'succeeded'}: status = 'succeeded'
        elif positive == {'rejected'}: status = 'rejected'
        else: status = 'unknown'
        return {'status': status, 'observation_ref': reference}
