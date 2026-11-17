"""Reject conflicting experiment identities without touching frozen inputs."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
import experiment_plan as ep
from study_contracts import verify
from study_policy import compare_arms, dispatch_allowed, stop_scope


class ExperimentContractTest(unittest.TestCase):
    def setUp(self):
        self.plan = ep.ROOT / 'experiments/plan-2-deepagent-refined-skills'
        self.study_path = ep.ROOT / 'studies/banking-architecture-comparison/study.json'
        self.study = ep.read(self.study_path)

    def assert_rejected(self, path, mutate):
        original = ep.read
        def changed(candidate):
            value = original(candidate)
            if Path(candidate) == path:
                mutate(value)
            return value
        with patch.object(ep, 'read', side_effect=changed):
            with self.assertRaises(ValueError):
                ep.validate(self.plan)

    def test_all_four_normal_bindings(self):
        results = [ep.validate(ep.ROOT / name) for name in self.study['arms']]
        self.assertEqual([r['task_count'] for r in results], [22] * 4)
        self.assertEqual([r['mode'] for r in results], ['single-agent', 'single-agent', 'slow-only', 'enforce'])
        self.assertTrue(all(not r['executable'] for r in results))

    def test_conflicting_plan_fields_fail_closed(self):
        changes = {'skill_release':'1.0.0', 'skill_manifest':'shared/skills/releases/1.0.0/release.json',
                   'comparison_trials':7, 'comparison_cases':21, 'mode':'shadow',
                   'comparison_language':'zh', 'seed':301, 'system_prompt_version':'baseline-v1',
                   'display_number':1, 'implementation':'different', 'unexpected_field':True,
                   'execution_enabled':True, 'comparison_ready':True}
        for field, value in changes.items():
            with self.subTest(field=field):
                self.assert_rejected(self.plan/'plan.json', lambda d, k=field, v=value:d.update({k:v}))

    def test_missing_and_nested_configuration_rejected(self):
        self.assert_rejected(self.plan/'plan.json', lambda d:d.pop('seed'))
        self.assert_rejected(self.plan/'plan.json', lambda d:d['limits'].update(max_steps=999))
        self.assert_rejected(self.plan/'plan.json', lambda d:d['model_profile'].update(temperature=.8))

    def test_study_total_and_duplicate_budget_rejected(self):
        self.assert_rejected(self.study_path, lambda d:d.update(total_formal_episodes=89))
        self.assert_rejected(self.study_path, lambda d:d.update(episode_timeout_seconds=10))
        self.assert_rejected(self.study_path, lambda d:d['arms'].__setitem__(0,d['arms'][1]))
        self.assert_rejected(self.study_path, lambda d:d.update(agent_hub_mode='shadow'))

    def test_plan_and_registry_cannot_disagree_with_manifest_identity(self):
        original = ep.read
        def changed(path):
            d = original(path)
            if Path(path) in [self.plan/'plan.json', self.study_path]:
                target = d if Path(path)==self.plan/'plan.json' else d['arm_bindings'][self.plan.name]
                target['skill_release']='1.0.0'
            return d
        with patch.object(ep,'read',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'Skill version/path'):
                ep.validate(self.plan)

    def test_oracles_and_business_inventory(self):
        result = verify()
        self.assertEqual(result['operations'],69)
        self.assertEqual(result['cases'],22)
        self.assertEqual(result['oracle_fixtures'],12)
        self.assertFalse(result['real_runtime_drivers_verified'])

    def test_stop_scope_isolated_vs_shared_and_unknown(self):
        self.assertEqual(stop_scope(self.study,'ordinary_business_failure'),'episode')
        self.assertEqual(stop_scope(self.study,'isolated_framework_violation'),'arm')
        self.assertEqual(stop_scope(self.study,'shared_environment_corruption'),'study')
        self.assertEqual(stop_scope(self.study,'unclassified_fault'),'study')

    def test_deadline_and_pause_cannot_dispatch(self):
        limits=self.study['limits']
        self.assertTrue(dispatch_allowed(2399,511,limits))
        self.assertFalse(dispatch_allowed(2400,0,limits))
        self.assertFalse(dispatch_allowed(1,512,limits))
        self.assertFalse(dispatch_allowed(1,0,limits,paused=True))
        # Resume receives the same elapsed total, never a new start budget.
        self.assertFalse(dispatch_allowed(2401,20,limits))

    def test_metric_examples_and_censoring(self):
        control=dict(planned=22,scored=22,passed=12,censored=False,severe_violations=0,wall_seconds=100)
        partial={**control,'scored':18}
        self.assertEqual(compare_arms(control,partial)['decision'],'no-observed-quality-uplift')
        improved={**control,'passed':15,'wall_seconds':200}
        out=compare_arms(control,improved)
        self.assertAlmostEqual(out['primary_delta'],3/22)
        self.assertEqual(out['wall_time_ratio'],2)
        self.assertEqual(out['decision'],'observed-single-round-quality-increase')
        self.assertEqual(compare_arms(control,{**improved,'censored':True})['decision'],'incomplete-no-ranking')
        self.assertEqual(compare_arms(control,{**improved,'scored':20})['decision'],
                         'uplift-claim-blocked-by-coverage-or-severe-violation')
        with self.assertRaises(ValueError):
            compare_arms(control,{**control,'passed':23})


if __name__ == '__main__':
    unittest.main()
