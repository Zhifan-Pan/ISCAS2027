"""Portable CLI for the unchanged seven-policy runtime; no cached prediction IO."""
from pathlib import Path
import argparse
import json
import os
import sys


def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--portable-root', type=Path, required=True)
    p.add_argument('--assets-config', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--selector-lock', type=Path, default=root / 'models/SELECTOR_LOCK.json')
    p.add_argument('--h3-model', type=Path)
    p.add_argument('--seed', type=int, choices=[101, 202, 303], default=101)
    p.add_argument('--policy', choices=['Native', 'RawTop1', 'B', 'NplusR', 'SplusR', 'Direct', 'H3Direct'], required=True)
    p.add_argument('--residency', choices=['matched', 'policy'], default='matched', help='matched loads both models as in the timing study; policy avoids loading PLL on no-PLL paths')
    args = p.parse_args()
    if args.output.exists():
        p.error('output already exists; choose a fresh destination')
    os.environ['ASR_REPRO_CONFIG'] = str(args.assets_config.resolve())
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    sys.path.insert(0, str(args.portable_root.resolve()))
    import torch
    import frozen_inference
    from runtime_v153 import SharedRuntime
    torch.set_num_threads(1)
    engine = frozen_inference.load_whisper_in_admitted_worker(args.seed)
    needs_pll = args.policy not in ['Native', 'RawTop1', 'H3Direct']
    pll = frozen_inference.load_pll_in_admitted_worker(batch=32) if needs_pll or args.residency == 'matched' else None
    normalizer = frozen_inference.load_vendor('wer_rules_v3')
    beta = json.loads(args.selector_lock.read_text())[str(args.seed)]['raw_beta']
    h3_file = args.h3_model or root / f'models/H3_{args.seed}.json'
    beta_h3 = json.loads(h3_file.read_text())['raw_beta']
    runtime = SharedRuntime(engine, pll, normalizer, beta, beta_h3)
    rows = json.loads(args.manifest.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    policy = 'SDirect' if args.policy == 'Direct' else args.policy
    with args.output.open('x') as out:
        for row in rows:
            value = runtime.run(row['path'], row['lang'], row['uid'], row['split'], policy)
            out.write(json.dumps({'id': row.get('anon_id', row['uid']), 'seed': args.seed, 'policy': args.policy, 'residency': args.residency, **value}, ensure_ascii=False) + '\n')
            out.flush()


if __name__ == '__main__':
    main()
