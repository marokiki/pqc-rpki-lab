#!/usr/bin/env python3
"""Recompute every pinned raw snapshot and compare complete document results.

Parallelism only partitions independent documents; it never scales aggregate
traffic. The ordinary evaluate.py rrdp command remains the sequential replay.
"""
import argparse
import concurrent.futures
import contextlib
import hashlib
import io
import json
import tempfile
from pathlib import Path
import evaluate

def one(args):
    path, scratch = args
    out = Path(scratch)/(path.stem+'.json')
    with contextlib.redirect_stdout(io.StringIO()):
        evaluate.analyze_rrdp([path], out, base=path.parent)
    return json.loads(out.read_text())

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--expected', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--workers', type=int, default=3, choices=range(1,9))
    a = p.parse_args()
    expected = json.loads(a.expected.read_text())
    paths = sorted(a.directory.glob('*.xml'))
    wanted = {x['path']:x for x in expected['documents']}
    if set(x.name for x in paths) != set(wanted):
        raise SystemExit('raw file set differs from expected snapshot set')
    verified = []
    with tempfile.TemporaryDirectory() as scratch:
        with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
            for result in pool.map(one, [(x,scratch) for x in paths]):
                if result['errors'] or len(result['documents']) != 1:
                    raise ValueError('snapshot analysis failed: '+str(result['errors']))
                row = result['documents'][0]
                if row != wanted[row['path']]:
                    raise ValueError('snapshot replay result mismatch: '+row['path'])
                verified.append(row['sha256'])
                print(f'Verified {len(verified)}/{len(paths)} snapshots', flush=True)
    output = {'status':'passed','method':'complete per-document DER and XML length replay from retained raw bodies',
        'documents':len(verified),'verified_body_sha256':sorted(verified),
        'expected_summary_sha256':hashlib.sha256(a.expected.read_bytes()).hexdigest()}
    a.out.write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':main()
