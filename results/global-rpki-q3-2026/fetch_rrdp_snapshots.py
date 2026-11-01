#!/usr/bin/env python3
"""Capture live RRDP snapshots; pin notification/hash/session/serial and UTC times.

This is a separate, dated cohort, never a substitute for September snapshots.
Use --replay-manifest to retrieve the exact immutable bodies or fail closed.
Raw XML stays in scratch storage; publish the manifest and notification files.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

from fetch_rrdp_day import HOSTS, PAT

NS = 'http://www.ripe.net/rpki/rrdp'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def notification(raw):
    root = ET.fromstring(raw)
    if root.tag != '{'+NS+'}notification' or root.get('version') != '1':
        raise ValueError('invalid RRDP notification root/version')
    snapshots = root.findall('{'+NS+'}snapshot')
    if len(snapshots) != 1:
        raise ValueError('notification must contain exactly one snapshot')
    item = snapshots[0]
    if urlsplit(item.get('uri', '')).scheme != 'https':
        raise ValueError('snapshot URI must use HTTPS')
    if not re.fullmatch('[0-9a-fA-F]{64}', item.get('hash', '')):
        raise ValueError('invalid snapshot hash')
    serial = int(root.attrib['serial'])
    if serial < 1:
        raise ValueError('invalid serial')
    return {'session_id': root.attrib['session_id'], 'serial': serial,
            'snapshot_uri': item.attrib['uri'], 'snapshot_sha256': item.attrib['hash'].lower()}

def download(url, path, limit):
    start = now()
    request = urllib.request.Request(url, headers={'Accept-Encoding': 'identity',
        'User-Agent': 'pqc-rpki-lab-research/1.0'})
    tmp = path.with_suffix(path.suffix+'.part')
    digest = hashlib.sha256(); count = 0
    try:
        with urllib.request.urlopen(request, timeout=90) as response, tmp.open('wb') as f:
            encoding = response.headers.get('Content-Encoding', 'identity')
            if encoding.lower() != 'identity':
                raise ValueError('unexpected Content-Encoding: '+encoding)
            for chunk in iter(lambda: response.read(1024*1024), b''):
                count += len(chunk)
                if count > limit:
                    raise ValueError('explicit response byte limit exceeded')
                digest.update(chunk); f.write(chunk)
            headers = {k: response.headers.get(k) for k in
                       ('Date', 'Content-Length', 'Content-Type', 'Content-Encoding', 'ETag', 'Last-Modified')}
            meta = {'requested_uri': url, 'final_uri': response.geturl(),
                    'started_utc': start, 'finished_utc': now(), 'http_status': response.status,
                    'response_headers': headers, 'bytes': count, 'sha256': digest.hexdigest()}
        if headers['Content-Length'] and int(headers['Content-Length']) != count:
            raise ValueError('Content-Length mismatch')
        tmp.replace(path)
        return meta
    finally:
        tmp.unlink(missing_ok=True)

def check_snapshot(path, expected):
    # Streaming root check; the full object parser subsequently checks every publish.
    with path.open('rb') as f:
        _, root = next(ET.iterparse(f, events=('start',)))
    if (root.tag != '{'+NS+'}snapshot' or root.get('version') != '1' or
        root.get('session_id') != expected['session_id'] or int(root.get('serial', '-1')) != expected['serial']):
        raise ValueError('snapshot root/session/serial mismatch')

def capture(url, out):
    ident = hashlib.sha256(url.encode()).hexdigest()[:20]
    row = {'notification_uri': url, 'notification_path': 'notifications/'+ident+'.xml'}
    try:
        n = out/row['notification_path']
        row['notification_response'] = download(url, n, 10_000_000)
        row.update(notification(n.read_bytes()))
        row['snapshot_path'] = 'xml/'+row['snapshot_sha256']+'.xml'
        path = out/row['snapshot_path']
        row['snapshot_response'] = download(row['snapshot_uri'], path, 2_000_000_000)
        if row['snapshot_response']['sha256'] != row['snapshot_sha256']:
            raise ValueError('snapshot SHA-256 does not match notification')
        check_snapshot(path, row)
        row['status'] = 'verified'
    except Exception as exc:
        if row.get('snapshot_path'):
            (out/row['snapshot_path']).unlink(missing_ok=True)
        row['status'] = 'unavailable'; row['error'] = str(exc)
    print(json.dumps({'uri': url, 'status': row['status'], 'bytes': row.get('snapshot_response', {}).get('bytes'), 'error': row.get('error')}), flush=True)
    return row

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--network', action='store_true', required=True)
    p.add_argument('--log', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--replay-manifest', type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/'notifications').mkdir(exist_ok=True); (a.out/'xml').mkdir(exist_ok=True)
    if a.replay_manifest:
        manifest = json.loads(a.replay_manifest.read_text())
        for row in manifest['endpoints']:
            if row['status'] != 'verified': continue
            path = a.out/row['snapshot_path']
            if not path.exists() or file_hash(path) != row['snapshot_sha256']:
                response = download(row['snapshot_uri'], path, 2_000_000_000)
                if response['sha256'] != row['snapshot_sha256']:
                    raise SystemExit('pinned snapshot hash mismatch')
            check_snapshot(path, row)
        print('Pinned snapshot bodies verified; no current-state substitution.')
        return
    if not a.log: p.error('--log or --replay-manifest is required')
    urls = set()
    for line in a.log.read_text().splitlines():
        m = PAT.match(line)
        if m and urlsplit(m.group(2)).hostname in HOSTS:
            urls.add(m.group(2))
    if not urls: raise SystemExit('empty endpoint selection')
    started = now()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda url: capture(url, a.out), sorted(urls)))
    manifest = {'classification': 'live snapshot cohort, separate from September cache and deltas',
        'started_utc': started, 'finished_utc': now(),
        'endpoint_selection': 'distinct notification URLs at the selected September delta hosts, observed in the 20260930 log',
        'selection_log_sha256': hashlib.sha256(a.log.read_bytes()).hexdigest(),
        'accept_encoding': 'identity', 'endpoints': rows,
        'snapshot_xml_bytes': sum(x.get('snapshot_response', {}).get('bytes', 0) for x in rows if x['status'] == 'verified')}
    (a.out/'rrdp-snapshot-selection.json').write_text(json.dumps(manifest, indent=2)+'\n')
    if any(x['status'] != 'verified' for x in rows):
        print('Partial coverage: inspect every unavailable endpoint in the manifest.', flush=True)

if __name__ == '__main__': main()
