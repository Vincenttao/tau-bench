"""Declared B-path metrics entrypoint; rejects a mislabeled A-path manifest."""
import argparse,json
from collect_metrics_v02 import collect
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args()
 result=collect(a.directory,implementation='runtime-moa-main-local-skill')
 print(json.dumps({'cards':len(result['metrics']),'facts':result['facts']},ensure_ascii=False,indent=2))
