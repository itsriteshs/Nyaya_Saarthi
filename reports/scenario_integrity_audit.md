# Scenario Integrity Audit
Source file audited: `scenario.csv` (the repo does not contain a separate `scenarios.csv`).
## Verdict
`scenario.csv` is connected to the rest of the dataset by valid IDs, but the rows are not all quality-clean. The main problems are exact/near duplicate scenario facts, repeated generic titles, and 42 rows that look out of the project scope from the supplied audit plan.
## Structural Checks
- scenario rows: 600
- missing required scenario cells: 0
- duplicate scenario ids: 0
- scenarios without narrative: 0
- narratives with invalid scenario_id: 0
- classifications.csv invalid narrative_id refs: 0
- entities.csv invalid narrative_id refs: 0
- events.csv invalid narrative_id refs: 0
- event_relations.csv invalid narrative_id refs: 0
- slot_annotations.csv invalid narrative_id refs: 0
- followup_questions.csv invalid narrative_id refs: 0
- clarification_answers.csv invalid narrative_id refs: 0
- gold_outputs invalid scenario_id refs: 0
- gold_outputs invalid narrative_id refs: 0
- event_relations invalid event refs: 0
- events invalid entity refs excluding NONE placeholders: 0

## Scenario Quality Findings
- Scenario rows: 600
- Missing required scenario cells: 0
- Duplicate scenario IDs: 0
- Exact duplicate `scenario_facts` groups: 3 (6 rows)
  - SCN000043, SCN000360: House burglary
  - SCN000054, SCN000526: Vehicle theft
  - SCN000066, SCN000314: Online phishing theft
- Duplicate/templated `scenario_title` groups: 166 (442 rows)
- Very high near-duplicate fact pairs at >=0.93 similarity: 280

## Likely Out-of-Scope Rows
- Restitution of conjugal rights: 18 rows: SCN000063, SCN000154, SCN000165, SCN000208, SCN000224, SCN000227, SCN000262, SCN000265, SCN000270, SCN000271, SCN000287, SCN000343, SCN000375, SCN000399, SCN000413, SCN000416, SCN000494, SCN000531
- Divorce proceedings conflict: 7 rows: SCN000094, SCN000139, SCN000225, SCN000327, SCN000350, SCN000409, SCN000532
- Alimony and maintenance claim: 8 rows: SCN000071, SCN000246, SCN000260, SCN000334, SCN000359, SCN000449, SCN000576, SCN000585
- Inheritance property claim: 9 rows: SCN000030, SCN000080, SCN000112, SCN000185, SCN000248, SCN000319, SCN000365, SCN000439, SCN000534

## Taxonomy Snapshot
- primary_incident_family: Cybercrime=80, Theft and robbery=80, Consumer Disputes=60, Assault & Threats=60, Property Disputes=60, Employment/Labour=50, Family Law=50, Miscellaneous=40, Traffic & Road Incidents=40, Financial Fraud=40, Domestic Violence=40
- incident_setting: Physical=363, Online=124, Hybrid=113
- jurisdiction_state: Delhi=79, Maharashtra=78, Gujarat=78, Tamil Nadu=77, Telangana=76, Karnataka=74, Uttar Pradesh=69, West Bengal=69
- split: challenge=158, train=150, test=148, validation=144

## Cross-File Notes
- Every scenario has exactly one narrative, and every narrative maps to a valid scenario.
- Every narrative has exactly one classification, and rough category-to-family checks found 0 obvious mismatches.
- Downstream tables are valid at the ID level, but they do not cover all narratives: entities/events/slots currently cover about 300 narratives, and gold outputs cover 300 scenarios. That is acceptable if these are selected annotation subsets, but it is not full coverage.
- `NONE` placeholders are used in event/entity link fields. They are placeholders, not foreign keys; excluding `NONE`, event entity references are valid.

## Recommended Repair
1. Remove or rewrite the 3 exact duplicate scenario-fact rows and the strongest near-duplicates.
2. Remove or re-scope the 42 civil/family/property rows listed above if the dataset scope is crime reporting and legal-navigation safety.
3. Rewrite repeated titles so title text is specific enough for browsing and annotation QA.
4. If scenarios are removed, cascade the change through narratives, classifications, selected annotations and gold outputs so no orphan records are introduced.
