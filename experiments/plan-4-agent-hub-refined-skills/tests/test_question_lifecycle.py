from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from episode_controller import EpisodeController
from input_router import RoutingPolicy
from task_session import JavaTask, durable_json


class Planner:
    def complete(self, purpose, state, schema):
        if not state['task']['goals']:
            return {'goals': [{'description': 'read balance', 'quote': state['content']}], 'existing_routes': []}
        return {'goals': [], 'existing_routes': [], 'context_quote': state['content']}


class Judge:
    def ask(self, request):
        answers = {key: {'type': 'noul', 'noul': .01 if key == 'no_business' or
            (key == 'has_new' and not request['state']['new_goal_proposals']) else .99} for key in request['questions']}
        return {'model': 'jev-1.14.0', 'answers': answers, 'usage': {'input_tokens': 1, 'output_tokens': 1}}


class QuestionLifecycleTests(unittest.TestCase):
    def test_duplicate_context_proposal_reaches_real_java_without_creating_or_completing_goals(self):
        class DuplicatePlanner(Planner):
            def complete(self, purpose, state, schema):
                if not state['task']['goals']: return super().complete(purpose, state, schema)
                goal = state['task']['goals'][0]['goal_id']
                return {'goals': [], 'existing_routes': [
                    {'goal_id': goal, 'action': 'context', 'quote': 'My income is 180000.'},
                    {'goal_id': goal, 'action': 'context', 'quote': 'I already have a subscription.'}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = self.controller(root, task); controller.planner = DuplicatePlanner()
                controller.user('m1', 'Read my balance', now=900)
                original = controller.state(900)['goals']
                result = controller.user('m2', 'My income is 180000. I already have a subscription.', now=900)
                self.assertEqual(result['status'], 'ready')
                self.assertTrue(result['context_only'])
                self.assertEqual(controller.state(900)['goals'], original)
                self.assertEqual(controller.bindings, {})
                self.assertEqual(len(list(controller.directory.glob('*.input-normalization.json'))), 1)

    def test_conflicting_duplicate_cannot_cancel_goal_through_normalization(self):
        class ConflictingPlanner(Planner):
            def complete(self, purpose, state, schema):
                if not state['task']['goals']: return super().complete(purpose, state, schema)
                goal = state['task']['goals'][0]['goal_id']
                return {'goals': [], 'existing_routes': [
                    {'goal_id': goal, 'action': 'context', 'quote': state['content']},
                    {'goal_id': goal, 'action': 'cancel', 'quote': state['content']}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = self.controller(root, task); controller.planner = ConflictingPlanner()
                controller.user('m1', 'Read my balance', now=900)
                result = controller.user('m2', 'Cancel it.', now=900)
                self.assertEqual(result['status'], 'clarify')
                self.assertEqual(controller.state(900)['goals'][0]['state'], 'active')
                self.assertFalse(controller.state(900)['can_dispatch'])
                self.assertEqual(controller.bindings, {})

    def controller(self, root, task):
        return EpisodeController(task, None, Planner(), Judge(), RoutingPolicy('fixture', .3, .7,
            'jev-latest', 'jev-1.14.0'), root/'control', {}, 'synthetic policy')

    def question(self, controller, text):
        controller.last_question = text
        durable_json(controller.directory/'last-question.json', {'question': text})
        controller.remember_assistant(text)

    def test_valid_context_reply_retires_orphaned_question_persistently_without_accepting_business(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = self.controller(root, task)
                controller.user('m1', 'Read my balance', now=900)
                self.question(controller, 'Please supply identity details.')
                result = controller.user('m2', 'My name is Synthetic Customer.', now=900)
                self.assertEqual(result['status'], 'ready')
                self.assertEqual(controller.last_question, '')
                self.assertEqual(controller.state(900)['goals'][0]['outcome'], 'undetermined')
                self.assertEqual(controller.bindings, {})
                self.assertTrue(any('Please supply identity details.' in item['content'] for item in controller.evidence.visible().values()))
            with JavaTask(root/'task', 'episode', 9999, 999) as task:
                self.assertEqual(self.controller(root, task).last_question, '')

    def test_real_confirmation_wait_survives_a_context_update_about_another_goal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = self.controller(root, task); controller.user('m1', 'Read my balance', now=900)
                first = controller.state(900)['goals'][0]['goal_id']
                task.call('receive', episode='episode', message='setup', content='Also replace the card')
                task.call('apply', message='setup', revision=controller.state(900)['revision'],
                    actions=[{'kind': 'new_goal', 'description': 'replace card'}])
                task.call('wait_goal', goal=first, revision=controller.state(900)['revision'], question='Confirm the specific operation?')
                self.question(controller, 'Confirm the specific operation?')
                controller.user('m2', 'My name is Synthetic Customer.', now=900)
                self.assertEqual(controller.last_question, 'Confirm the specific operation?')
                self.assertEqual(next(g for g in controller.state(900)['goals'] if g['goal_id'] == first)['state'], 'waiting')

    def test_clarification_prompt_uses_live_waits_instead_of_old_question_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with JavaTask(root/'task', 'episode', 1000, 64) as task:
                controller = self.controller(root, task); controller.user('m1', 'Read my balance', now=900)
                self.question(controller, 'Old identity question?')
                prompt = controller.clarification_prompt(now=900)
                self.assertNotIn('Old identity question?', prompt)
                goal = controller.state(900)['goals'][0]['goal_id']
                task.call('wait_goal', goal=goal, revision=controller.state(900)['revision'], question='Actual outstanding confirmation?')
                self.assertIn('Actual outstanding confirmation?', controller.clarification_prompt(now=900))
                self.assertEqual(task.call('message_status', message='m1')['status'], 'applied')
