# RPKIへのPQC署名導入に関する詳細評価・先行研究比較・採用提案

> EXPERIMENTAL / NOT FOR PRODUCTION
> 評価基盤復旧日: 2026-06-15

## 1. 結論

現時点でSIDROPS向けの最初の実装・相互運用プロファイルとして提案すべき方式は
**ML-DSA-65**である。ただし、純粋なrepository sizeと検証性能では
**Falcon-512が最も有力な対抗候補**であり、FN-DSA、X.509、CMS、provider、
HSM、validator実装が成熟した時点で主候補を再判定すべきである。

| 用途 | 提案 |
|---|---|
| 最初のSIDROPS実験用MTI | ML-DSA-65 |
| 性能優先の高優先度比較 | Falcon-512 |
| Category 5比較 | ML-DSA-87、Falcon-1024 |
| 暗号方式の多様性・stress test | SLH-DSA |
| NIST Round 3研究比較 | MAYO、SNOVA、HAWK |
| 移行 | RSA/PQC parallel publicationとVRP equivalence telemetry |

ML-DSA-65を選ぶ理由は最小・最速だからではない。FIPS 204、RFC 9881、
RFC 9882により、X.509/CMSへ接続する標準経路が現時点で最も明確だからである。

## 2. 比較対象

| Algorithm | Category | Public key | Signature | Status |
|---|---:|---:|---:|---|
| RSA-2048/SHA-256 | classical | 270 B | 256 B | baseline |
| ML-DSA-65 | 3 | 1,952 B | 3,309 B | standardized |
| ML-DSA-87 | 5 | 2,592 B | 4,627 B | standardized |
| SLH-DSA-SHAKE-128s | 1 | 32 B | 7,856 B | standardized |
| SLH-DSA-SHAKE-192s | 3 | 48 B | 16,224 B | standardized |
| Falcon-512 | 1 | 897 B | 最大666 B | experimental |
| Falcon-1024 | 5 | 1,793 B | 最大1,280 B | experimental |
| MAYO-1 | 1 | 1,420 B | 454 B | NIST Round 3 |
| SNOVA-(24,5,4) | 1 | 1,016 B | 248 B | NIST Round 3 |
| HAWK-512 | 1 | 1,024 B | 最大555 B | metadata-only |

## 3. 測定方法

primitive benchmarkは32 byte messageに対するkeygen/sign/verifyの中央値を取る。
RSAはcryptography、PQCはoqs-python/liboqsを優先し、未導入時はOpenSSL
default providerへfallbackする。OpenSSL CLI値にはprocess起動時間を含む。これはASN.1、CMS、
certificate path、filesystem、cacheを含まないためvalidator全体の時間ではない。

repository impactはCA certificate、EE certificate、CRL、manifest、ROAの
synthetic corpusへ公開鍵・署名サイズを代入する。世界全体の較正値は2025年の
先行研究で観測されたrepository 838,030,450 bytes、public key 393,427個、
signature 788,916個を使用する。

## 4. Primitive benchmark

最新値は`results/primitive-bench.csv`を一次資料とする。2026-06-10の復旧前測定では
ML-DSA-65 sign約0.24 ms、verify約0.061 ms、Falcon-512 sign約2.04 ms、
verify約0.024 msだった。Falcon署名は可変長なのでrepository推定には最大長を使う。

SLH-DSA-128sのsignは約380 ms、192sは約679 msであり、CAの大量再発行に不利である。
MAYO-1とSNOVAは高速かつcompactだが、標準化途中なので運用採用の根拠にはできない。

## 5. 先行研究との比較

| Algorithm | 較正repository | RSA比 | 公表validation CPU |
|---|---:|---:|---:|
| RSA-2048 | 838 MB | 1.00x | 13.0 s |
| ML-DSA-65 | 3.91 GB | 4.66x | 51.8 s |
| ML-DSA-87 | 5.20 GB | 6.20x | 80.9 s |
| SLH-DSA-128s | 6.74 GB | 8.04x | 1,376.3 s |
| Falcon-512 | 1.41 GB | 1.68x | 23.4 s |
| Falcon-1024 | 2.24 GB | 2.68x | 46.4 s |
| MAYO-1 | 1.45 GB | 1.73x | 44.3 s |
| SNOVA-(24,5,4) | 1.12 GB | 1.34x | 47.3 s |
| HAWK-512 | 1.37 GB | 1.63x | 42.8 s |

較正式は公表された丸め値を概ね再現する。synthetic modelとの差は方式により
約5から16%で、主因は実RPKIとsynthetic corpusのsignature/public-key密度の差である。
論文・I-Dで世界全体への影響を示す場合は較正値を使うべきである。

primitive timingはCPUと実装最適化に依存する。特にFalconやSLH-DSAでは先行研究の
cycle換算値との差が大きいため、採用判断では実validator内測定を追加する必要がある。

## 6. RRDP、rsync、cache

size-dependentなRRDP snapshot transferはrepository sizeにほぼ比例する。
先行研究の約55.3 MB/sを単純適用すると、ML-DSA-65は約68秒、Falcon-512は約24秒、
SNOVAは約20秒相当になる。ただし通知取得、XML parse、Base64、TLS、session reset、
delta適用を含む総更新時間ではない。

日常運用ではdeltaが中心だが、初回同期、cache再構築、RRDP session reset、
backup、CDN egressでは全体サイズが直接効く。今後は実RRDP XML/gzip wire bytesと
rsync block transferを測定する必要がある。

## 7. ROAサイズ

現行ROA中央値2,125 Bから非暗号部分を1,341 Bと仮定すると、ML-DSA-65は
約9,911 B、Falcon-512は約3,570 B、MAYO-1は約3,669 B、SNOVAは約2,853 Bになる。
SLH-DSA-192sは約33,837 Bであり、通常のROA profileには過大である。

Null Schemeは冗長なEE公開鍵・署名を削減し得るが、新しい署名意味論とsecurity
reviewを必要とする。PQC導入の前提条件にはせず、独立した最適化として扱う。

## 8. 標準化と実装成熟度

ML-DSAはFIPS 204、X.509のRFC 9881、CMSのRFC 9882が存在する。SLH-DSAも
FIPS 205とPKIX/CMS仕様が存在するが、サイズとCPU負荷が大きい。

Falconはliboqsでprimitive測定可能だが、最終FN-DSAとRPKI-readyなPKIX/CMS経路の
相互運用を本基盤では確認していない。MAYO、SNOVA、HAWKはNISTが2026-05-14に
発表したAdditional Digital Signatures Round 3の研究候補であり、最終標準ではない。
HAWKは固定したliboqs 0.15.0/OpenSSL 3.6.2で利用できないためunsupportedとする。

## 9. RFC-profiled object generation feasibility

OpenSSL 3.6.2 default providerで、RFC 3779のIP/AS resource extension、
RPKI certificate policy、SIA、KeyUsage、BasicConstraintsを含むCA/EE証明書と
CRLを生成した。秘密鍵と中間生成物は自動削除される一時ディレクトリだけに置いた。

| Algorithm | CA certificate | EE certificate | CRL | CMS SignedData |
|---|---:|---:|---:|---|
| RSA-2048/SHA-256 | 1,038 B | 984 B | 381 B | 1,492 B、generic CMS |
| ML-DSA-65 | 5,767 B | 5,713 B | 3,430 B | unsupported |
| ML-DSA-87 | 7,725 B | 7,671 B | 4,748 B | unsupported |
| SLH-DSA-SHAKE-128s | 8,390 B | 8,336 B | 7,977 B | unsupported |
| SLH-DSA-SHAKE-192s | 16,774 B | 16,720 B | 16,345 B | unsupported |

PQC CMSでは`CMS_add1_signer:no default digest`が発生した。これはOID未認識ではなく、
OpenSSL CMS signerがpure ML-DSA/SLH-DSA鍵にdigestを選択できない実装境界である。
このためRFC 6488 MFT/ROAは生成していない。ASN.1 payloadを自作して迂回することも
行っていない。次の実装課題はRFC 9882/9814対応CMS backendと既存MFT/ROA
payload generatorの接続である。

## 10. Validator・real cache状況

Routinator、rpki-client、FORTは現在の環境に存在せず、存在確認、RSA baseline、
PQC object、VRP出力の各段階を`unsupported`として記録した。production TALや
network fetchは実行していない。

real RPKI cacheも指定されていないため`skipped`である。従ってrepository/RRDP値は
引き続きsyntheticまたはliterature-calibratedであり、実測と混同してはならない。

## 11. 移行提案

1. isolated TALでRSA branchとPQC branchを同じ意味内容から生成する。
2. certificate、CRL、manifest、ROAを複数validatorで検証する。
3. prefix、maxLength、origin AS、TA/sourceでVRP集合を比較する。
4. RSA parent/PQC child、PQC parent/RSA childを試験する。
5. stale manifest、inconsistent ROA、unsupported validatorを注入する。
6. repository、RRDP delta、cache、CPU、RSSを測定する。
7. telemetryとvalidator普及率に基づくRSA停止条件を定義する。

Composite signaturesを最初の必須経路にしない。parallel publicationの方がlegacy
validatorの挙動、branch別failure、VRP semantic divergenceを分離して観測できる。

## 12. Internet-Draftへの反映

- ML-DSA-65を最初の実験用algorithm suite候補とする。
- RFC 9881/9882のpure ML-DSAを参照し、旧Dilithium encodingを混在させない。
- ROA等のeContent semanticsとRTR/router側は変更しない。
- unsupported algorithmをsilent fallbackしない。
- stale manifestやCRL failureを別branchの成功で隠さない。
- initial sync、cache reset、oversized objectのresource limitを議論する。
- Falconは高優先度の別実験profile、Round 3候補はinformative比較に留める。

## 13. 未解決課題

1. RFC 9882/9814対応CMS SignedDataとMFT/ROA生成。
2. Routinator、rpki-client、FORTでの相互運用。
3. validator process内の検証benchmark。
4. 実corpusでのRRDP delta、rsync、cache測定。
5. TAL transition、rollback、mixed hierarchy policy。
6. HSMでのML-DSA/Falcon support。
7. FN-DSAおよびNIST Round 3候補の仕様変更追跡。

## 14. 最終判断

- **採用する:** ML-DSA-65を実験用MTIおよびSIDROPS主提案とする。
- **最優先で並行評価する:** Falcon-512。
- **比較用:** ML-DSA-87、Falcon-1024。
- **通常採用しない:** SLH-DSA-128s/192s。
- **研究比較のみ:** MAYO-1、SNOVA、HAWKその他Round 3候補。
- **production移行条件:** 複数validatorでの実object相互運用と実RRDP/cache測定。

## 15. 参照資料

- NIST FIPS 204、FIPS 205
- RFC 6480、6487、6488、6489、6916、7935、8182、9286、9582、9691
- RFC 9881、9882、9909、9814
- NIST Additional Digital Signature Schemes Round 3
- Thijs de Cock, *Post-Quantum Cryptography for the RPKI*, 2025
- draft-ietf-lamps-pq-composite-sigs
- draft-ietf-lamps-cms-composite-sigs
- draft-doesburg-sidrops-nullscheme
