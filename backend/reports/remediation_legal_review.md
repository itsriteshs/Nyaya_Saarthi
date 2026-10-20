# Legal coverage remediation and qualified-review queue

Checked 20 October 2026. This is a review proposal, not a legal approval. No source or provision was promoted to VERIFIED. Existing VERIFIED flags describe the dataset and do not establish independent legal correctness or live URL authenticity.

## Safe technical correction

`procedures.csv`, physical row 26, `PROC_CONTEST_ECHALLAN_COURT` had 21 values for 22 columns. Inserting an empty deadline before the explicitly fee-labelled value restores all subsequent typed fields. All original strings, the source ID and NOT_VERIFIED status are retained. The original and repaired values are in `experiments/manifests/remediation_procedure_repair.json`. Parsed procedures increase 29 → 30; eligible procedures remain zero.

The speed table originally had **no review_status column**. The technical repair appends an explicit NOT_VERIFIED flag to all 30 records, preserving every existing value; the original hash and operation are recorded in `experiments/manifests/remediation_speed_review_schema.json`. A last_verified_at timestamp cannot establish record-level legal approval. Records remain unverified even where a central source is later reviewed. There is no executable reviewed speed lookup in the rule engine.

## Seven unavailable provisions

| Record | Precise current exclusion | Required resolution |
|---|---|---|
| PROV_MVA_S129 | Amendment source lacks URL, review date and verification; source is only PARTIALLY_COMMENCED | Locate the amended text, prescribed standards/exceptions and section-specific commencement; qualified review of the recorded 2022 effective date. |
| PROV_MVA_S177 | Same four source blockers | Review residual-penalty applicability and amendment commencement; do not infer a fine for a specific incident. |
| PROV_MVA_S184 | Same source blockers, plus provision NOT_VERIFIED | Compare the complete amended penalty clause, minimum/maximum ranges, repeat conditions and enumerated dangerous acts. |
| PROV_MVA_S185 | Same source blockers, plus provision NOT_VERIFIED | Review test conditions, drugs/alcohol alternatives, repeat conditions and complete penalty text. |
| PROV_MVA_S194B | Same four source blockers | Review seat-belt and child-restraint subclauses and commencement. |
| PROV_BNS_S106_1 | PARTIALLY_COMMENCED source and provision NOT_VERIFIED | Correct a substantive text error for legal review: the current dataset adds a prompt-reporting condition to subsection (1). The official government text instead describes causing death by a rash/negligent act and separately provides a medical-practitioner exception. Do not merge the flight/reporting condition from subsection (2). |
| PROV_BNS_S106_2 | PARTIALLY_COMMENCED source, UNDER_REVIEW provision, PENDING_COMMENCEMENT active status | Remain excluded. The 2024 commencement notification expressly excepted this subsection. Establish any subsequent commencement from a current authoritative instrument before considering eligibility. |

The first five records share SRC_MVAA_2019, which has blank official_url and last_verified_at, NOT_VERIFIED review and PARTIALLY_COMMENCED status. SRC_BNS_2023 is dataset-VERIFIED but PARTIALLY_COMMENCED; its stored MHA PDF URL returned 404 during lookup. A source-wide FULLY_COMMENCED flag would be an unsafe way to admit commenced subsections: a future reviewed schema must support provision-specific commencement with instrument provenance.

## Authoritative lookup evidence and proposed changes

These sources are **review inputs only**, outside the admitted corpus. Search-index excerpts were available where noted; failed direct fetches are not evidence of reviewed source contents.

1. [India Code: Motor Vehicles (Amendment) Act, 2019](https://www.indiacode.nic.in/repealedfileopen?rfilename=A2019-32.pdf). The indexed Act identifies commencement by notification, potentially on different dates for different provisions. Direct PDF retrieval timed out. Proposed action: retrieve and archive the authentic Act and each relevant commencement notification; then review individual provision versions. Do not fill a single blanket commencement flag from the Act's enactment date.
2. [India Code consolidated Motor Vehicles Act](https://www.indiacode.nic.in/bitstream/123456789/19009/1/aaa1988___59.pdf). Indexed text includes amendment footnotes and effective dates. Proposed action: compare full clauses and exceptions, distinguishing a duty provision from its separate penalty provision. OFF_NO_LICENCE points to section 3 while its own text says the penalty is under section 181, absent from the provision table. This is a substantive relationship gap, not a safe ID substitution.
3. [Official Gazette copy of S.O. 1522(E), hosted by Chhattisgarh Transport](https://cgtransport.gov.in/GadgetPDF_File/06042018_Draft_Notification_no_S_O_1522E_dated_6_4_2018_regarding_Revised_Speed_Limits_0.pdf), supported by the [MoRTH parliamentary answer hosted by PIB](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1539335&lang=2&reg=48) and [2021 Lok Sabha answer](https://sansad.in/getFile/loksabhaquestions/annex/175/AU3813.pdf?source=pqals). Proposed action: reconcile vehicle seating/category definitions and road classes against each of the 30 rows, then check supersession, state/local notifications, signage and date applicability. In particular, the HPMV expressway row records 80, while the published central M2/M3 passenger category table records 100: category equivalence and applicability require review, not automatic replacement. Review the M1 row's asserted detection tolerance against the full notification before retaining it. No numeric limit is admitted here.
4. [Government statutory text: BNS section 106](https://www.incometaxindia.gov.in/w/section-106-101). Proposed action: replace the erroneous subsection (1) paraphrase with a reviewed account of the complete clause, retaining the medical exception and distinguishing subsection (2). This government-hosted text is a corroborating review source, not an automatic policy allowlist addition.
5. [MHA indexed commencement notification, 23 February 2024](https://www.mha.gov.in/sites/default/files/BhartiyaNyayaSanhita_24022024.pdf) and [MHA 2025–26 annual report](https://www.mha.gov.in/sites/default/files/AREnglish_24032026.pdf). The indexed notification excepts subsection 106(2); the indexed annual report repeats that exception. Direct notification retrieval returned 404. Proposed action: locate a durable primary Gazette copy, check subsequent notifications, and record provision-specific commencement before review. These excerpts do not establish its current October 2026 legal status independently.

## All procedures, penalties and speed records

`experiments/metrics/remediation_legal_current.json` lists every record, physical row, source ID, exclusion reason and resolution category. Counts overlap: 26 procedures are not verified, 25 have unverified required records, 24 have unresolved services, 24 lack steps, 23 lack a legal basis, four have unresolved step/document references, two have unresolved required references, and two have an ineligible legal basis. Source-level blockers also apply. Fixing CSV parseability does not repair any substantive reference.

OFF_NO_PUC still has a blank source ID and pending provision; most other penalty rows rely on unverified sources or missing penalty provisions. No penalty claim becomes eligible. No reference is guessed, and no external source lookup is treated as legal review.

## Responsible answer boundary

Before and after: four of eleven provisions are eligible (sections 3, 39, 112 and 146); six sources have eligible dataset flags; no affirmative procedure, numeric penalty or numeric speed-limit record is eligible. With confirmed date, jurisdiction and relevant facts, the system can offer qualified general licensing, registration, speed-regulation and insurance information from those four records. It cannot responsibly determine guilt, an actual applicable fine, a road-specific numeric limit, deadlines, affirmative filing/payment instructions, or the legal correctness of translated free-form model prose. Sparse coverage and pending review must remain visible, with deterministic abstention/fallback.
