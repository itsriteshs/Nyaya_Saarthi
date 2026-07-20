# Classifications Rebuild Note

Updated `classifications.csv` after `narratives.csv` expanded to 1,500 rows.

## What Changed
- Rebuilt `classifications.csv` to contain one classification for every final narrative.
- Preserved scenario-level `primary_incident_family` as `primary_category` across English, Hindi, Hindi-Latin and paraphrase variants.
- Preserved each scenario's `secondary_issue_labels` inside `secondary_categories`.
- Recomputed `procedural_intents`, `user_goal`, `urgency_class`, `current_danger`, `ongoing_incident`, `incident_medium`, property/threat/injury flags and `recommended_route` from `scenario.csv` plus narrative-level completeness/uncertainty.
- Added `clarification_needed` intent for low-completeness or uncertain narratives.
- Used consistent enum-style values for urgency, medium, time status and booleans.
- Left `reviewer_id` blank because the rebuilt labels are system-derived and not human-reviewed.

## Validation
- Classification rows: 1,500.
- Narrative rows: 1,500.
- Duplicate `classification_id`: 0.
- Invalid `classification_id` format: 0.
- Invalid `narrative_id` references: 0.
- Narratives missing classification: 0.
- Duplicate classifications per narrative: 0.
- Category preservation errors against `scenario.csv`: 0.
- Parent translation/paraphrase category mismatches: 0.
- Enum consistency errors: 0.
- Current-danger consistency errors: 0.
- Ongoing-incident consistency errors: 0.
- Low-completeness narratives missing `clarification_needed`: 0.

## Coverage
- English classified narratives: 750.
- Devanagari Hindi classified narratives: 600.
- Hindi-Latin classified narratives: 150.
