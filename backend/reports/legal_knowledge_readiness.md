# Legal knowledge readiness (Phase 4)

Computed from the current 23 source files in `data/Dataset 2` by `app.services.legal.guidance.readiness()`. The source fingerprint is `b0521a641e94c970ab3b12b41f66357705feae5acbcf0d3d84cc9dc21ed2cb2c`. Counts represent local dataset metadata and relationships; they do not establish independent legal authentication.

| Table | Loaded | Eligible for affirmative use | Main restriction |
|---|---:|---:|---|
| Legal sources | 18 | 6 | 11 lack `VERIFIED` review; 8 lack an admissible official URL; the partly commenced BNS source is conditional. Overlapping reasons. |
| Legal provisions | 11 | 4 | 7 excluded or conditional because of source, review, or status. |
| Rule logic | 30 | 13 marked `VERIFIED` | Rule applicability is matter specific. Several reviewed rules have unsupported conditions, exceptions or missing required facts. |
| Procedures | 29 parseable of 30 physical records | 0 | 25 not reviewed; 24 unresolved service IDs; 22 missing basis IDs. Overlapping reasons. |
| Offences and penalties | 30 | 0 usable penalty records | No row clears offence review and both eligible source and provision linkage. |
| Speed limits | 30 | 0 reviewed numeric limits | No row level legal review status; numeric speed advice is withheld. |

Eligible sources: `SRC_MVA_1988`, `SRC_CMVR_1989`, `SRC_BNSS_2023`, `SRC_LSAA_1987`, `SRC_NHA_1956`, `SRC_CPA_2019`.

Eligible provisions: `PROV_MVA_S3`, `PROV_MVA_S39`, `PROV_MVA_S112`, `PROV_MVA_S146`. Retrieval still requires a confirmed jurisdiction and event date. Eligibility means dataset reviewed, primary source metadata, official host URL, and supported temporal and jurisdiction scope; the linked site was not fetched or authenticated live.

The loader excludes malformed physical row 26 of `procedures.csv`. Phase 1 also identified an unresolved required source ID in `offences_penalties.csv`. Raw datasets were not changed. The 143 placeholder references and 28 unresolved references in the Phase 1 inventory remain data curation work; the loader and policy do not fill them in. In particular, the `SVC_VAHAN_PENDING_ADD` placeholder keeps otherwise reviewed registration procedures out of guidance. The speed notification is under review, blocking a speed threshold even though the base Motor Vehicles Act speed provision is eligible.

Core workflow implications:

- **Speeding:** May surface section 112 as potentially relevant when date and jurisdiction are known; numeric limits, sign specific conclusions, penalties, and rule matches remain unestablished.
- **Challan:** No reviewed residual penalty rule can be evaluated safely; challan procedures and amounts are withheld.
- **Licence:** Section 3 can be retrieved; dataset rule predicates and vehicle class relationships can still block an applicability match.
- **Registration:** Section 39 can be retrieved; registration procedures are blocked by unresolved service or legal basis links.
- **Insurance:** Section 146 can be retrieved; a rule match needs confirmed insurance status and vehicle class. No penalty is stated.
- **Accident:** Related relief, reporting and procedural records lack eligible linked evidence. Phase 3 urgent assistance remains separate from legal conclusions.

The 11 multilingual explanation records remain under legal or language review, so Phase 4 guidance is English and flags the limitation for Hindi or Hinglish matters.
