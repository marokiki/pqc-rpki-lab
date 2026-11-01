#!/usr/bin/env python3
"""Trace-preserving DER length projections; never generates valid PQ signatures.

Run from any directory. Uses only Python's standard library and the repository's
existing DER/CMS parser. No old evidence or Internet-Draft is modified.
"""
from __future__ import annotations
import argparse, base64, collections, csv, gzip, hashlib, io, json, re, statistics
import sys, tarfile, xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from pqc_rpki_lab import der
from pqc_rpki_lab.cms import parse_one, decode_oid, parse_all

RSA_KEY='1.2.840.113549.1.1.1'
RSA_SIG='1.2.840.113549.1.1.11'
SHA256='2.16.840.1.101.3.4.2.1'
SHA512='2.16.840.1.101.3.4.2.3'
SIGNED_DATA='1.2.840.113549.1.7.2'
MESSAGE_DIGEST='1.2.840.113549.1.9.4'
BASE_LOCATIONS={
 'rpki.arin.net':'arin.net','rpki.ripe.net':'ripe.net','rpki.apnic.net':'apnic.net',
 'rpki-repo.registro.br':'registro.br','repository.lacnic.net':'lacnic.net',
 'rpki-rsync.us-east-2.amazonaws.com':'amazonaws.com','rpki.afrinic.net':'afrinic.net',
 'rpki-rsync.idnic.net':'idnic.net','rsync.paas.rpki.ripe.net':'paas.ripe.net',
 'rpki-rps.cnnic.cn':'rps.cnnic.cn','rpki-repository.nic.ad.jp':'nic.ad.jp',
 'rsync.fiti.net.cn':'fiti.net.cn','rpki-rps.arin.net':'rps.arin.net','rpkica.twnic.tw':'twnic.tw'}

@dataclass(frozen=True)
class Suite:
    name:str
    oid:str
    key_bytes:int
    signature_bytes:int

SUITES={
 'rsa':Suite('RSA-2048/SHA-256',RSA_SIG,270,256),
 'ml-dsa-44':Suite('ML-DSA-44','2.16.840.1.101.3.4.3.17',1312,2420),
 'ml-dsa-65':Suite('ML-DSA-65','2.16.840.1.101.3.4.3.18',1952,3309),
 'composite-mldsa65-p256':Suite('ML-DSA-65/P-256','1.3.6.1.5.5.7.6.45',2017,3381),
}

def sha256(data): return hashlib.sha256(data).hexdigest()
def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def write_json(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def node(data):
    n,end=parse_one(data)
    if end!=len(data):raise ValueError('trailing DER data')
    return n

def oid(algorithm):return decode_oid(algorithm.children()[0])
def alg(suite):return der.algorithm_identifier(suite.oid)
def rebuild(n,children):return der.tlv(n.tag,b''.join(children))
def certificate_info(data):
    root=node(data).children(); tbs=root[0].children()
    offset=1 if tbs[0].tag==0xa0 else 0
    spki=tbs[offset+5].children()
    info={'ski':None,'aki':None,'is_ca':False,'subject_key_oid':oid(spki[0]),'signature_oid':oid(root[1]),
          'signature_bytes':len(root[2].value)-1,'spki_bytes':len(tbs[offset+5].encoded)}
    for field in tbs:
        if field.tag!=0xa3:continue
        for extension in field.children()[0].children():
            ef=extension.children(); eo=decode_oid(ef[0]); value=node(ef[-1].value)
            if eo=='2.5.29.14':info['ski']=value.value.hex()
            elif eo=='2.5.29.35':
                for a in value.children():
                    if a.tag==0x80:info['aki']=a.value.hex()
            elif eo=='2.5.29.19':info['is_ca']=any(x.tag==1 and x.value!=b'\x00' for x in value.children())
    return info

def check_rsa_signature(algorithm):
    if oid(algorithm)!=RSA_SIG:raise ValueError('source RPKI signature is not RSA/SHA-256: '+oid(algorithm))

def project_certificate(data,subject_suite,issuer_suite):
    if subject_suite=='rsa' and issuer_suite=='rsa':return data
    n=node(data); root=n.children(); tbs=root[0].children(); off=int(tbs[0].tag==0xa0)
    fields=[x.encoded for x in tbs]
    if subject_suite!='rsa':
        spki=tbs[off+5].children()
        if oid(spki[0])==RSA_KEY:
            su=SUITES[subject_suite]
            fields[off+5]=der.sequence(alg(su),der.bit_string(bytes(su.key_bytes)))
        # BGPsec router ECDSA subject keys remain governed by BGPsec, not RPKI signatures.
    if issuer_suite=='rsa':
        signature_algorithm=root[1].encoded; signature=root[2].encoded
    else:
        check_rsa_signature(root[1]); su=SUITES[issuer_suite]
        fields[off+1]=alg(su); signature_algorithm=alg(su)
        signature=der.bit_string(bytes(su.signature_bytes))
    return der.sequence(rebuild(root[0],fields),signature_algorithm,signature)

def crl_info(data):
    root=node(data).children(); fields=root[0].children(); info={'aki':None,'revoked_entries':0}
    for f in fields:
        if f.tag==0xa0:
            for ext in f.children()[0].children():
                parts=ext.children()
                if decode_oid(parts[0])=='2.5.29.35':
                    for child in node(parts[-1].value).children():
                        if child.tag==0x80:info['aki']=child.value.hex()
    # revokedCertificates follows thisUpdate and optional nextUpdate.
    pos=1 if fields[0].tag==2 else 0
    pos+=2
    if pos<len(fields) and fields[pos].tag in (0x17,0x18):pos+=1
    if pos<len(fields) and fields[pos].tag in (0x17,0x18):pos+=1
    if pos<len(fields) and fields[pos].tag==0x30:info['revoked_entries']=len(fields[pos].children())
    return info

def project_crl(data,suite):
    if suite=='rsa':return data
    r=node(data).children(); t=r[0].children(); off=int(t[0].tag==2); check_rsa_signature(r[1])
    fields=[x.encoded for x in t];fields[off]=alg(SUITES[suite])
    return der.sequence(rebuild(r[0],fields),alg(SUITES[suite]),der.bit_string(bytes(SUITES[suite].signature_bytes)))

def cms_parts(data):
    ci=node(data).children()
    if decode_oid(ci[0])!=SIGNED_DATA:raise ValueError('not CMS SignedData')
    sd=ci[1].children()[0].children()
    certsets=[(i,x) for i,x in enumerate(sd) if x.tag==0xa0]
    if len(certsets)!=1 or len(certsets[0][1].children())!=1:raise ValueError('expected one embedded EE certificate')
    eci=sd[2].children(); ec=eci[1].children()[0].value
    signers=sd[-1].children()
    if len(signers)!=1:raise ValueError('expected one CMS signer')
    return ci,sd,certsets[0][0],signers[0].children(),ec

def project_cms(data,suite):
    if suite=='rsa':return data
    ci,sd,certindex,si,ec=cms_parts(data)
    if len(si)!=6 or si[3].tag!=0xa0:raise ValueError('unexpected RPKI SignerInfo layout')
    su=SUITES[suite];sf=[x.encoded for x in sd]
    sf[1]=der.set_of(der.algorithm_identifier(SHA512))
    sf[certindex]=der.tlv(0xa0,project_certificate(sd[certindex].children()[0].encoded,suite,suite))
    attrs=[]
    for attr in si[3].children():
        parts=attr.children()
        if decode_oid(parts[0])==MESSAGE_DIGEST:
            attrs.append(der.sequence(parts[0].encoded,der.set_of(der.octet_string(bytes(64)))))
        else:attrs.append(attr.encoded)
    check=oid(si[4])
    if check not in (RSA_KEY,RSA_SIG):raise ValueError('non-RSA CMS signature: '+check)
    signer=[x.encoded for x in si]
    signer[2]=der.algorithm_identifier(SHA512)
    signer[3]=der.tlv(0xa0,b''.join(sorted(attrs)))
    signer[4]=alg(su);signer[5]=der.octet_string(bytes(su.signature_bytes))
    sf[-1]=der.set_of(der.sequence(*signer))
    return der.sequence(ci[0].encoded,der.tlv(0xa0,der.sequence(*sf)))

def object_info(data,kind):
    if kind=='cer':return certificate_info(data)
    if kind=='crl':return crl_info(data)
    ci,sd,idx,si,ec=cms_parts(data)
    info=certificate_info(sd[idx].children()[0].encoded)
    info['is_ca']=False
    info['econtent_bytes']=len(ec)
    if kind=='mft':
        from pqc_rpki_lab.rpki_asn1 import parse_manifest_econtent
        info['manifest_entries']=len(parse_manifest_econtent(ec)['entries'])
    return info

def projected(data,kind,suite,boundary=False):
    if kind=='cer':return project_certificate(data,suite,'rsa' if boundary else suite)
    if kind=='crl':return project_crl(data,suite)
    return project_cms(data,suite)

def classify(name):return Path(name).suffix.lstrip('.').lower()
def snapshot_uri(name):
    relative=name.split('/data/',1)[1]
    return relative if relative.startswith('ta/') else 'rsync://'+relative

def analyze_snapshot(archive,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=[]; skipped=collections.Counter(); parse_errors=[]; total_candidates=0; baseline_by_kind=collections.defaultdict(list)
    with tarfile.open(archive,'r|gz') as tar:
        for entry in tar:
            if not entry.isfile() or '/data/' not in entry.name:continue
            kind=classify(entry.name)
            if kind not in ('cer','crl','roa','mft','asa','gbr','rsc','tak','spl'):
                skipped[kind]+=1;continue
            total_candidates+=1
            data=tar.extractfile(entry).read()
            uri=snapshot_uri(entry.name)
            rec={'uri':uri,'type':kind,'bytes':len(data),'sha256':sha256(data),'host':urlsplit(uri).hostname or '_trust_anchors','is_trust_anchor_cache_member':uri.startswith('ta/')}
            try:
                rec.update(object_info(data,kind))
                rec['sizes']={k:len(projected(data,kind,k)) for k in SUITES}
                assert rec['sizes']['rsa']==len(data)
                if kind=='cer' and rec['is_ca']:
                    rec['boundary_sizes']={k:len(projected(data,kind,k,True)) for k in SUITES}
            except (ValueError,IndexError,UnicodeError) as e:
                rec['error']=str(e);parse_errors.append({'uri':uri,'bytes':len(data),'error':str(e)})
            records.append(rec);baseline_by_kind[kind].append(len(data))
    with gzip.open(out/'snapshot-inventory.jsonl.gz','wt') as f:
        for rec in records:f.write(json.dumps(rec,separators=(',',':'))+'\n')
    cas={r['ski']:r for r in records if r.get('is_ca') and r.get('ski')}
    ancestors={}
    def lineage(key):
        if key in ancestors:return ancestors[key]
        seen=set();path=[]
        while key in cas and key not in seen:
            seen.add(key);path.append(key)
            parent=cas[key].get('aki')
            if parent==key:break
            key=parent
        return path
    subtree_bytes=collections.Counter()
    for r in records:
        for key in lineage(r.get('aki')):subtree_bytes[key]+=r['bytes']
    candidates=[key for key,c in cas.items() if c.get('aki') in cas and c.get('aki')!=key]
    selected=max(candidates,key=lambda k:(subtree_bytes[k],k)) if candidates else None
    migrated={k for k in cas if selected in lineage(k)} if selected else set()
    baseline=sum(r['bytes'] for r in records)
    summary={'classification':'one validated-cache snapshot, not the report merged global dataset',
      'snapshot_name':Path(archive).name,'archive_sha256':file_hash(archive),'archive_bytes':Path(archive).stat().st_size,
      'object_count':len(records),'object_bytes':baseline,'skipped_nonobject_members':dict(skipped),
      'parse_errors':parse_errors,'object_sizes':{},'by_location':{},'projections':{},
      'hierarchy':{'ca_certificates':len(cas),'ca_keys_with_missing_parent':sum(c.get('aki') not in cas for c in cas.values()),
        'mixed_selection':'largest observed non-self-issued CA subtree with a known parent; hypothetical scenario',
        'selected_ca_ski':selected,'selected_ca_uri':cas[selected]['uri'] if selected else None,
        'selected_parent_ski':cas[selected].get('aki') if selected else None,'migrated_ca_keys':len(migrated)}}
    for kind,values in baseline_by_kind.items():
        summary['object_sizes'][kind]={'count':len(values),'bytes':sum(values),'median_bytes':statistics.median(values),'mean_bytes':statistics.mean(values),'min_bytes':min(values),'max_bytes':max(values)}
    for r in records:
        loc=BASE_LOCATIONS.get(r['host'],r['host'])
        group=summary['by_location'].setdefault(loc,{'count':0,'bytes':0,'types':{}})
        group['count']+=1;group['bytes']+=r['bytes'];group['types'][r['type']]=group['types'].get(r['type'],0)+1
    for suite in SUITES:
        full=0;mixed=0;affected=0
        for r in records:
            if 'sizes' not in r:continue
            full+=r['sizes'][suite]
            if r.get('aki') in migrated:
                mixed+=r['sizes'][suite];affected+=1
            elif r.get('is_ca') and r.get('ski') in migrated:
                mixed+=r['boundary_sizes'][suite];affected+=1
            else:mixed+=r['bytes']
        usable=bool(records) and not parse_errors
        summary['projections'][suite]={'status':'estimated' if usable else 'incomplete' if records else 'unavailable','full_replacement_bytes':full if usable else None,
          'idealized_parallel_publication_bytes':baseline+full if usable else None,
          'mixed_tree_bytes':mixed if usable else None,'mixed_affected_objects':affected,
          'excluded_object_bytes':sum(e['bytes'] for e in parse_errors)}
    write_json(out/'snapshot-summary.json',summary)
    print(json.dumps({k:summary[k] for k in ('object_count','object_bytes','object_sizes','hierarchy','projections')},indent=2))


def analyze_rrdp(paths,out,base=None):
    rows=[];seen=set();totals=collections.Counter();sizes=collections.Counter();errors=[]
    for path in sorted(paths):
        path=Path(path);original_bytes=path.stat().st_size;digest=file_hash(path)
        public_path=str(path.relative_to(base)) if base is not None else path.name
        if digest in seen:continue
        seen.add(digest)
        try:
            stream=ET.iterparse(path,events=('start','end'))
            _,xml=next(stream);kind=xml.tag.rsplit('}',1)[-1]
            if kind not in ('snapshot','delta'):continue
            if xml.tag!='{http://www.ripe.net/rpki/rrdp}'+kind or xml.get('version')!='1':
                raise ValueError('invalid RRDP namespace/version')
            session_id=xml.attrib['session_id'];serial=int(xml.attrib['serial'])
            growth=collections.Counter();counts=collections.Counter();withdrawals=0;replacements=0;published_bytes=0
            unmodeled=[];non_der_bytes=0
            snapshot_uris=set()
            for event,item in stream:
                if event!='end' or item is xml:continue
                local=item.tag.rsplit('}',1)[-1]
                if item.tag!='{http://www.ripe.net/rpki/rrdp}'+local:raise ValueError('invalid element namespace')
                if local=='withdraw':
                    if kind=='snapshot':raise ValueError('withdraw in snapshot')
                    withdrawals+=1;xml.clear();continue
                if local!='publish':raise ValueError('unexpected RRDP element')
                if kind=='snapshot':
                    if 'hash' in item.attrib:raise ValueError('replacement hash in snapshot')
                    uri=item.attrib['uri']
                    if uri in snapshot_uris:raise ValueError('duplicate snapshot URI')
                    snapshot_uris.add(uri)
                encoded=''.join((item.text or '').split())
                data=base64.b64decode(encoded,validate=True);typ=classify(item.attrib['uri']);counts[typ]+=1
                if 'hash' in item.attrib:replacements+=1
                published_bytes+=len(data)
                if typ=='tal':
                    # A public server also publishes a text TAL in its RRDP snapshot.
                    # Its future key/URI contents are outside this signed-object model.
                    non_der_bytes+=len(data)
                    unmodeled.append({'uri':item.attrib['uri'],'type':typ,'bytes':len(data),
                        'sha256':sha256(data),'treatment':'opaque text TAL retained at observed size; future TAL contents not modeled'})
                for suite in SUITES:
                    new=data if typ=='tal' else projected(data,typ,suite)
                    growth[suite]+=4*((len(new)+2)//3)-len(encoded)
                xml.clear()
            row={'path':public_path,'sha256':digest,'kind':kind,'session_id':session_id,'serial':serial,
                'original_xml_bytes':original_bytes,'publish_counts':dict(counts),'withdraw_count':withdrawals,
                'replacement_publish_count':replacements,'published_der_bytes':published_bytes-non_der_bytes,
                'unmodeled_payloads':unmodeled,
                'projected_xml_bytes':{k:original_bytes+growth[k] for k in SUITES}}
            assert row['projected_xml_bytes']['rsa']==original_bytes
            rows.append(row)
            totals[kind+'_documents']+=1;totals[kind+'_xml_bytes']+=original_bytes
            totals[kind+'_withdrawals']+=withdrawals;totals[kind+'_replacement_publishes']+=replacements
            for typ,count in counts.items():totals[kind+'_publish_'+typ]+=count
            for suite,n in row['projected_xml_bytes'].items():sizes[kind+'_'+suite]+=n
        except (ValueError,IndexError,ET.ParseError,KeyError) as e:
            errors.append({'path':public_path,'sha256':digest,'error':str(e)})
    result={'classification':'observed archive documents, not per-client network traffic',
       'method':'preserve original XML framing, URIs, whitespace, and withdrawal elements; replace base64 payload length using re-encoded complete DER lengths',
       'totals':dict(totals),'projections':dict(sizes),'errors':errors,'documents':rows,
       'status':'incomplete' if errors else 'estimated' if rows else 'unavailable'}
    write_json(out,result);print(json.dumps({'totals':dict(totals),'projections':dict(sizes),'errors':errors[:10],'error_count':len(errors)},indent=2))


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('snapshot');s.add_argument('archive',type=Path);s.add_argument('--out',type=Path,required=True)
    s=sub.add_parser('rrdp');s.add_argument('directory',type=Path);s.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.command=='snapshot':analyze_snapshot(a.archive,a.out)
    else:analyze_rrdp(a.directory.rglob('*.xml'),a.out,base=a.directory)
if __name__=='__main__':main()
