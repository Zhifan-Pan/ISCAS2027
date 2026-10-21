"""Replay released numeric acceptor evidence into a NEW external directory.

Default: recompute the 96 policies, 480 language rows and fixed bootstrap.
Optional --fit-all: reproduce the nine DEV fits from the same released numbers.
The optional fit replay creates an explicitly post-result transport plan; it
does not replace the historical scientific lock or count as a new study.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
import numpy as np

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--acceptor-root', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--fit-all', action='store_true')
    a = p.parse_args(); root = a.acceptor_root.resolve(); out = a.output_dir.resolve()
    assert root not in out.parents and out != root, 'Output must be outside input tree'
    assert not out.exists(), 'Refuse to overwrite an existing output directory'
    manifest = json.loads((root/'PACKAGING_IDENTITY.json').read_text())
    for name, item in manifest['numeric_inputs'].items():
        assert sha(root/'inputs'/name) == item['released_sha256'], name
    out.mkdir(parents=True)
    (out/'results').mkdir(); (out/'counts').mkdir(); (out/'cv').mkdir()
    plan = json.loads((root/'prerefit_plan.json').read_text())
    if a.fit_all:
        plan['DEV_input_sha256'] = {str(s): sha(root/'inputs'/f'DEV_{s}.npz') for s in [101,202,303]}
        plan['replay_execution_note'] = ('Post-result numeric replay plan. The inherited choices were locked before the original CV; '
                                         'this transport file is not a new prefit registration. Only input identities change.')
        (out/'prerefit_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
        (out/'models').mkdir()
        for family in ['H4','HR4','H3']:
            for seed in [101,202,303]:
                subprocess.run([sys.executable,str(root/'tools/fit_acceptor.py'),'--root',str(out),
                                '--data-root',str(root/'inputs'),'--family',family,'--seed',str(seed)],check=True)
        # A refit is not used silently for the canonical replay. Report it separately.
        refit_comparison = []
        for f in (root/'models').glob('H*.json'):
            old=json.loads(f.read_text()); new=json.loads((out/'models'/f.name).read_text())
            refit_comparison.append({'model':f.name,'same_selected_lambda':old['lambda']==new['lambda'],
                                     'beta_max_abs_diff':float(np.max(np.abs(np.asarray(old['raw_beta'])-new['raw_beta']))),
                                     'OOF_difference':new['selected_OOF_macro_WER']-old['selected_OOF_macro_WER']})
        (out/'REFIT_COMPARISON.json').write_text(json.dumps(refit_comparison,indent=2)+'\n')
        print('Optional refits complete; canonical evaluation remains available via the default command.')
        return
    shutil.copy2(root/'prerefit_plan.json',out/'prerefit_plan.json')
    shutil.copytree(root/'models',out/'models')
    with (out/'stdout.log').open('w') as log:
        subprocess.run([sys.executable,str(root/'tools/evaluate_acceptors.py'),'--root',str(out),
                        '--data-root',str(root/'inputs')],stdout=log,stderr=subprocess.STDOUT,check=True)
    checks=[]
    for name in ['policy_summary.csv','per_language_SDIN.csv','three_checkpoint_means.json','primary_comparisons.json']:
        assert (out/'results'/name).read_bytes()==(root/'expected'/name).read_bytes(),name
        checks.append(name)
    for name in ['bootstrap_draws.npz']:
        with np.load(out/'results'/name,allow_pickle=False) as g, np.load(root/'expected'/name,allow_pickle=False) as e:
            assert g.files == e.files
            for k in g.files: np.testing.assert_array_equal(g[k],e[k])
        checks.append(name)
    for f in (root/'counts').glob('*.npz'):
        with np.load(out/'counts'/f.name,allow_pickle=False) as g, np.load(f,allow_pickle=False) as e:
            assert set(g.files)==set(e.files)
            for k in e.files: np.testing.assert_array_equal(g[k],e[k])
        checks.append('counts/'+f.name)
    receipt={'status':'EXACT_NUMERIC_REPLAY','checks':checks,'generated_dir':str(out),
             'inherited_plan_sha256':manifest['historical_plan_sha256'],
             'released_plan_sha256':sha(root/'prerefit_plan.json'),
             'scope':'Numeric policies and paired statistics only; not new training, timing, ASR or independence certification.'}
    (out/'REPLAY_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'checked_files':len(checks)}))

if __name__=='__main__': main()
