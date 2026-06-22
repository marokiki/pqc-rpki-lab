# Signed Object Scope

ROAs, Manifests, ASPAs, RSCs, and TAKs use the RFC 6488 CMS signed-object template. The PQC profile should apply one signature algorithm suite uniformly to these object types unless object-specific evidence justifies an exception. Certificates and CRLs use their respective RPKI profiles but belong to the same repository algorithm suite.

BGPsec UPDATE signatures are not RFC 6488 signed objects. They have router-side signing, verification, and BGP message-size constraints and are outside this profile. BGPsec router certificates remain RPKI certificates; excluding BGPsec UPDATE signing does not exclude those certificates from certificate-profile analysis.
