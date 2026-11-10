#!/usr/bin/env python3
"""Tests for the AI Workforce scripts. Standard library only: python3 -m unittest discover -s tests -v"""
import csv, datetime as dt, json, math, os, random, subprocess, sys, tempfile, unittest, xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AW = os.path.join(ROOT, 'ai-workforce')
PY = sys.executable


def run(skill, script, *args, ok=(0,)):
    p = subprocess.run([PY, os.path.join(AW, skill, 'scripts', script), *args], capture_output=True, text=True,
                       cwd=os.path.join(AW, skill), env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if p.returncode not in ok:
        raise AssertionError(f'{script} exited {p.returncode}\n{p.stdout}\n{p.stderr}')
    return p.stdout


class DataSynthesizer(unittest.TestCase):
    def test_reproducible_and_in_range(self):
        a = run('data-synthesizer', 'synth.py', 'generate', 'examples/customers.schema.json', '--rows', '300')
        b = run('data-synthesizer', 'synth.py', 'generate', 'examples/customers.schema.json', '--rows', '300')
        self.assertEqual(a, b)
        rows = list(csv.DictReader(a.splitlines()))
        self.assertEqual(len(rows), 300)
        self.assertTrue(all(18 <= int(r['age']) <= 85 for r in rows))
        self.assertTrue(all(r['email'].endswith('@example.com') for r in rows))
        nulls = sum(1 for r in rows if not r['last_feedback']) / len(rows)
        self.assertTrue(0.25 < nulls < 0.55, nulls)

    def test_profile_never_copies_free_text(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'real.csv')
            with open(src, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f); w.writerow(['name', 'city', 'note'])
                for i in range(40):
                    w.writerow([f'Person {i}', 'Lyon' if i % 2 else 'Paris', f'secret note {i}'])
                w.writerow(['Rare Person', 'Brest', 'unique'])
            out = run('data-synthesizer', 'synth.py', 'profile', src)
            schema = json.loads(out)
            self.assertNotIn('secret note', out)
            self.assertNotIn('Brest', out)  # rare category grouped as OTHER
            city = next(c for c in schema['columns'] if c['name'] == 'city')
            self.assertIn('OTHER', city['values'])


class DataForecaster(unittest.TestCase):
    def test_picks_seasonal_and_interval_contains_point(self):
        res = json.loads(run('data-forecaster', 'forecast.py', 'examples/monthly_sales.csv', '--value-col', 'sales', '--horizon', '6', '--json'))
        self.assertTrue(res['method'].startswith('seasonal'))
        self.assertEqual(len(res['forecast']), 6)
        for f in res['forecast']:
            self.assertLessEqual(f['low80'], f['value']); self.assertLessEqual(f['value'], f['high80'])


class AnomalyDetector(unittest.TestCase):
    def test_finds_spike_gap_and_shift(self):
        out = json.loads(run('anomaly-detector', 'anomalies.py', 'examples/api_latency.csv', '--value-col', 'response_ms',
                             '--expect-every', '15', '--json', ok=(1,)))
        kinds = {a['kind'] for a in out['anomalies']}
        self.assertTrue({'spike', 'missing_data', 'level_shift_up'} <= kinds, kinds)

    def test_quiet_series_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 's.csv'); r = random.Random(1); t0 = dt.datetime(2026, 1, 1)
            with open(p, 'w') as f:
                f.write('ts,value\n')
                for i in range(80):
                    f.write(f'{(t0 + dt.timedelta(hours=i)).isoformat()},{100 + r.gauss(0, 2):.2f}\n')
            run('anomaly-detector', 'anomalies.py', p, '--threshold', '6', ok=(0,))


class DecisionOptimizer(unittest.TestCase):
    def test_constraints_and_ranking(self):
        res = json.loads(run('decision-optimizer', 'decide.py', 'examples/crm_choice.json', '--json'))
        self.assertEqual(res['ranking'][0]['name'], 'CRM Alpha')
        self.assertEqual([d['name'] for d in res['dropped']], ['CRM Delta'])
        self.assertTrue(res['robust'])
        self.assertIn('CRM Beta', res['closest_flip'])


class DigitalSimulation(unittest.TestCase):
    def test_probabilities_and_what_if(self):
        base = json.loads(run('digital-simulation', 'simulate.py', 'examples/launch_model.json', '--runs', '4000', '--json'))
        hi = json.loads(run('digital-simulation', 'simulate.py', 'examples/launch_model.json', '--runs', '4000', '--set', 'price=199', '--json'))
        p0, p1 = base['outputs']['profit']['prob_above_0'], hi['outputs']['profit']['prob_above_0']
        self.assertTrue(0.6 < p0 < 0.95, p0)
        self.assertGreater(p1, p0)
        again = json.loads(run('digital-simulation', 'simulate.py', 'examples/launch_model.json', '--runs', '4000', '--json'))
        self.assertEqual(base, again)

    def test_unsafe_formula_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'm.json')
            json.dump({'inputs': {'x': {'value': 1}}, 'outputs': {'y': "__import__('os').getcwd()"}}, open(p, 'w'))
            with self.assertRaises(AssertionError):
                run('digital-simulation', 'simulate.py', p, '--runs', '1')


class DigitalTwin(unittest.TestCase):
    def test_alert_stale_and_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, 'state.json')
            run('digital-twin', 'twin.py', 'update', 'examples/cold_room.spec.json', 'examples/readings.csv', '--state', st,
                '--now', '2026-11-10T09:10:00', ok=(2,))
            s = json.load(open(st))
            self.assertEqual(s['status'], 'alert')
            self.assertEqual(s['signals']['temp_c']['status'], 'alert')
            self.assertEqual(s['signals']['humidity_pct']['status'], 'stale')
            self.assertEqual(s['ignored_signals'], ['vibration_mm_s'])


class TrendWatcher(unittest.TestCase):
    def test_new_topic_emerges_and_fixed_bug_fades(self):
        res = json.loads(run('trend-watcher', 'trends.py', 'examples/support_tickets.csv', '--json'))
        top = ' '.join([res['emerging'][i]['term'] for i in range(4)] + sum((x['also'] for x in res['emerging'][:4]), []))
        self.assertTrue('sms' in top or 'two-factor' in top or 'bank sync' in top, top)
        fading = ' '.join(x['term'] + ' ' + ' '.join(x['also']) for x in res['fading'])
        self.assertIn('vat', fading)


class EngagementAssessor(unittest.TestCase):
    def test_funnel_and_bounds(self):
        res = json.loads(run('engagement-assessor', 'engagement.py', 'examples/events.csv', '--funnel', 'signup,first_project,invite_sent', '--json'))
        f = [x['users'] for x in res['funnel']]
        self.assertEqual(f[0], res['users_total'])
        self.assertTrue(f[0] >= f[1] >= f[2] > 0)
        self.assertTrue(0 <= res['stickiness_dau_mau_pct'] <= 100)
        self.assertTrue(all(c['retention_pct'][0] == 100 for c in res['cohorts']))


class DataVisualizer(unittest.TestCase):
    def test_svgs_are_valid_and_accessible(self):
        with tempfile.TemporaryDirectory() as d:
            for kind, csvf, x, y in (('line', 'signups.csv', 'month', 'signups,paid'), ('bar', 'signups.csv', 'month', 'signups'), ('hbar', 'channels.csv', 'channel', 'leads')):
                out = os.path.join(d, kind + '.svg')
                run('data-visualizer', 'chart.py', 'examples/' + csvf, '--x', x, '--y', y, '--type', kind, '--title', 'T', '--out', out)
                doc = xml.dom.minidom.parse(out)
                self.assertTrue(doc.getElementsByTagName('title') and doc.getElementsByTagName('desc'))


class ContentGuardian(unittest.TestCase):
    def test_findings_and_masking(self):
        res = json.loads(run('content-guardian', 'guard.py', 'examples/user_post.txt', '--policy', 'examples/policy.json', '--json', ok=(1,)))
        kinds = {f['kind'] for f in res}
        self.assertTrue({'email', 'iban', 'card_number', 'prompt_injection', 'policy_blocked', 'policy_review'} <= kinds, kinds)
        self.assertFalse(any('4539 1488' in f['excerpt'] for f in res))

    def test_no_false_card_on_random_digits(self):
        p = subprocess.run([PY, os.path.join(AW, 'content-guardian', 'scripts', 'guard.py'), '-', '--json'], input='Order 1234 5678 9012 3456 shipped on 2026-11-10.',
                           capture_output=True, text=True)
        self.assertNotIn('card_number', p.stdout)


class EngagementBooster(unittest.TestCase):
    def test_sample_size_matches_formula(self):
        out = run('engagement-booster', 'abtest.py', 'size', '--baseline', '0.10', '--mde', '0.02')
        n = int(out.split('Needed: ')[1].split(' ')[0].replace(',', ''))
        self.assertTrue(3800 <= n <= 3900, n)  # textbook value about 3,840

    def test_verdicts(self):
        self.assertIn('wins', run('engagement-booster', 'abtest.py', 'read', '--control', '2400,288', '--variant', '2380,345'))
        self.assertIn('no detectable', run('engagement-booster', 'abtest.py', 'read', '--control', '2400,288', '--variant', '2400,292'))
        self.assertIn('too few', run('engagement-booster', 'abtest.py', 'read', '--control', '100,5', '--variant', '100,12'))


class JourneyPersonalizer(unittest.TestCase):
    def test_report_and_explain(self):
        out = run('journey-personalizer', 'personalize.py', 'examples/users.csv', 'examples/rules.json')
        self.assertIn('nobody matches', out)
        self.assertIn('overlap', out)
        self.assertIn('EXCLUDED', out)
        self.assertIn('Assigned:', run('journey-personalizer', 'personalize.py', 'examples/users.csv', 'examples/rules.json', '--explain', 'u7'))


class WorkflowAutomaton(unittest.TestCase):
    def test_retry_and_escalation(self):
        with tempfile.TemporaryDirectory() as d:
            log, esc = os.path.join(d, 'runs.jsonl'), os.path.join(d, 'esc.md')
            base = ['--log', log, '--escalate-file', esc, '--backoff', '0.01']
            run('workflow-automaton', 'run_guarded.py', '--name', 'ok', *base, '--', PY, '-c', 'print(1)')
            run('workflow-automaton', 'run_guarded.py', '--name', 'flaky', '--retries', '2', *base, '--', PY, '-c', "import sys; print('HTTP 503'); sys.exit(1)", ok=(1,))
            run('workflow-automaton', 'run_guarded.py', '--name', 'auth', *base, '--', PY, '-c', "import sys; print('401 Unauthorized'); sys.exit(1)", ok=(1,))
            lines = [json.loads(l) for l in open(log)]
            self.assertEqual(sum(1 for l in lines if l['task'] == 'flaky'), 3)
            self.assertEqual(sum(1 for l in lines if l['task'] == 'auth'), 1)
            note = open(esc, encoding='utf-8').read()
            self.assertIn('flaky needs a human', note); self.assertIn('auth (exit code 1', note)


if __name__ == '__main__':
    unittest.main()
