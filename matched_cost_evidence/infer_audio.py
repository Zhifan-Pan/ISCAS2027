"""Parameterized raw-audio inference entry; no candidate-cache substitution.
Run under the local site's genuine GPU lease wrapper where required. Asset,
portable-helper, manifest and coefficient paths are explicit CLI parameters.
This entry is for output reproduction; formal latency uses the paired worker.
"""
from pathlib import Path
import argparse,os,sys,json

def main():
 p=argparse.ArgumentParser();p.add_argument('--portable-root',type=Path,required=True);p.add_argument('--assets-config',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--selector-lock',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--policy',choices=['NplusR','SplusR'],required=True);p.add_argument('--seed',type=int,default=101);args=p.parse_args()
 os.environ['ASR_REPRO_CONFIG']=str(args.assets_config.resolve());os.environ['TOKENIZERS_PARALLELISM']='false';sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(args.portable_root.resolve()))
 import torch,frozen_inference
 from runtime import SharedRuntime
 torch.set_num_threads(1);engine=frozen_inference.load_whisper_in_admitted_worker(args.seed);pll=frozen_inference.load_pll_in_admitted_worker(batch=32);norm=frozen_inference.load_vendor('wer_rules_v3');beta=json.loads(args.selector_lock.read_text())[str(args.seed)]['raw_beta'];rt=SharedRuntime(engine,pll,norm,beta);rows=json.loads(args.manifest.read_text());args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('w') as out:
  for row in rows:
   r=rt.run(row['path'],row['lang'],row['uid'],row['split'],args.policy);out.write(json.dumps({'id':row.get('anon_id',row['uid']),'policy':args.policy,'seed':args.seed,**r},ensure_ascii=False)+'\n');out.flush()
if __name__=='__main__':main()
