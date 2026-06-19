# Internet-Draft Submission Checklist

> EXPERIMENTAL / NOT FOR PRODUCTION

Submission target: `draft-yoshikawa-sidrops-pqc-rpki-00.xml`

This is an individual submission intended for discussion in SIDROPS. It is not
yet a SIDROPS Working Group document. Do not rename it to
`draft-ietf-sidrops-...` unless the WG adopts the work and the chairs request a
WG `-00` submission.

## Submission Objects

- `draft-yoshikawa-sidrops-pqc-rpki-00.md`: review copy generated from the authoring source.
- `draft-yoshikawa-sidrops-pqc-rpki-00.xml`: standalone RFCXML v3 submission source.
- `draft-yoshikawa-sidrops-pqc-rpki-00.txt`: xml2rfc-rendered plaintext.

The XML file is authoritative. The Datatracker generates its own text and HTML
renderings from it. The local HTML rendering is a validation output and is not
part of the published evidence snapshot. Uploading the local text rendering is
optional.

## 1. Before Submission

1. Create or verify the author's IETF Datatracker account using
   `segre@marokiki.net`: <https://datatracker.ietf.org/accounts/create/>.
2. Review the IETF Note Well and contribution rights before uploading:
   <https://www.ietf.org/about/note-well/>.
3. Subscribe to the SIDROPS list before starting the WG discussion:
   <https://www.ietf.org/mailman/listinfo/sidrops>.
4. Confirm that the draft still uses the individual name
   `draft-yoshikawa-sidrops-pqc-rpki-00` and has no `updates:` relationship.
5. Confirm author metadata: Tomoki Yoshikawa, Graduate School of Informatics,
   Kyoto University, `segre@marokiki.net`.
6. Review the abstract, intended status, IANA considerations, security
   considerations, references, and all `TBD` or placeholder text.
7. Check the current submission cutoff at <https://datatracker.ietf.org/submit/>.

The cutoff displayed on 2026-06-18 for new drafts before the next meeting is
2026-07-06 23:59 UTC (2026-07-07 08:59 JST). Treat the Datatracker page as
authoritative because meeting cutoffs change.

## 2. Rebuild and Validate

Run from the repository root immediately before submission:

```sh
.venv/bin/python tools/render_draft_submission.py
.venv/bin/xml2rfc \
  --cache .xml2rfc-cache \
  --text --html \
  --path ietf/submission \
  ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml
.venv/bin/python -m pytest -q
git diff --check
```

Then inspect both renderings. In particular, confirm the title page, author
address, expiry date, table of contents, references, and page breaks:

- `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.html`
- `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.txt`

Optionally run the server-side-equivalent checks through IETF Author Tools:
<https://author-tools.ietf.org/>. The Datatracker will run validation again
during upload.

## 3. Upload to Datatracker

1. Sign in at <https://datatracker.ietf.org/accounts/login/>. Signing in with
   the author account avoids an unnecessary email-authentication round trip.
2. Open <https://datatracker.ietf.org/submit/>.
3. Select
   `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml` as the XML source.
4. Do not set a replacement draft for this initial submission.
5. The plaintext file may be omitted; Datatracker will render it from XML.
6. Upload and review every extracted field and validation result. Check the
   draft name, revision `00`, title, author, email, date, intended status, and
   page count.
7. Do not use **Adjust metadata** merely to fix source mistakes. Cancel, fix the
   source, rebuild, and upload again. Adjustment invokes manual Secretariat
   processing and is intended for metadata that cannot be parsed correctly.
8. Select the author identity and choose **Post now**.

For an individual `-00`, no SIDROPS chair approval is required to post it. A
chair approval is required for an initial WG-named `draft-ietf-sidrops-...-00`.

If not authenticated as the author, Datatracker sends a confirmation message to
the authors listed in the draft. Follow its link; the draft is not published
until that confirmation is completed. Manual-post problems should be sent to
`support@ietf.org` with the standalone XML and the reason manual handling is
needed.

## 4. Confirm Publication

After posting:

1. Check the submission status at <https://datatracker.ietf.org/submit/status/>.
2. Confirm the document page appears at
   <https://datatracker.ietf.org/doc/draft-yoshikawa-sidrops-pqc-rpki/>.
3. Confirm XML, text, and HTML renderings are downloadable and visually sane.
4. Confirm receipt of the I-D Action announcement. Datatracker normally sends
   it shortly after posting.
5. Record the posted URL and revision in the repository. Do not modify the
   contents of an already-posted `-00`; corrections become `-01`.

An Internet-Draft normally expires after 185 days unless replaced, updated, or
kept active by a later process state.

## 5. Start SIDROPS Discussion

Send a concise message to `sidrops@ietf.org` after the I-D Action appears.
Suggested structure:

```text
Subject: New I-D: Post-Quantum Signature Algorithm Profile and Migration Considerations for RPKI

Hello SIDROPS,

I have submitted draft-yoshikawa-sidrops-pqc-rpki-00:
https://datatracker.ietf.org/doc/draft-yoshikawa-sidrops-pqc-rpki/

The draft proposes an experimental RPKI post-quantum signature profile and
migration framework. It uses ML-DSA-65 as the primary candidate, keeps
Falcon/FN-DSA and other candidates outside the mandatory path pending stable
PKIX/CMS profiles and validator evidence, and separates detailed measurements
into a reproducible experiment repository.

Feedback is particularly requested on:
- whether the work should define one suite or a migration framework;
- certificate, CRL, CMS signed-object, and manifest profile requirements;
- algorithm identifiers and IANA implications;
- validator interoperability and downgrade behavior; and
- evidence required before considering WG adoption.

Regards,
Tomoki Yoshikawa
```

Do not request WG adoption in the first announcement unless there has already
been substantive list discussion and implementation review. First seek review,
revise the individual draft, and present implementation evidence. SIDROPS'
charter states that protocol specifications should demonstrate at least two
interoperable implementations before being sent to the IESG.

## 6. Later Revisions and WG Adoption

- Corrections to the individual draft increment sequentially: `-01`, `-02`, and
  so on. A posted draft revision cannot be replaced in place.
- If SIDROPS adopts the work, create the WG document under the name requested by
  the chairs, normally `draft-ietf-sidrops-pqc-rpki-00`. The WG document starts
  at `-00` regardless of the individual draft's last revision.
- Mark the WG draft as replacing the individual draft during submission. The
  chairs verify the replacement and approve the WG `-00`.
- WG adoption does not publish an RFC. The document still proceeds through WG
  review, implementation/interoperability evidence, WG Last Call, Area Director
  review, IETF Last Call, IESG evaluation, and RFC Editor processing.

## Official References

- I-D submission guidance: <https://authors.ietf.org/submitting-your-internet-draft>
- Datatracker submission instructions: <https://datatracker.ietf.org/submit/tool-instructions/>
- Document validation: <https://authors.ietf.org/document-validation>
- Draft naming: <https://authors.ietf.org/naming-your-internet-draft>
- SIDROPS charter and contact details: <https://datatracker.ietf.org/wg/sidrops/about/>
