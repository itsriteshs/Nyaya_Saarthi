# Narratives Expansion Note

Updated `narratives.csv` in place from the 600 existing English narratives to 1,500 total narrative rows.

## What Changed
- Retained the 600 existing English narratives as the approved parent layer.
- Added 600 Devanagari Hindi narratives, one for every scenario in `scenario.csv`.
- Added 300 additional challenge variants across Hindi-Latin/Hinglish, emotional, incomplete, noisy, fragmented and out-of-order styles.
- Linked Hindi rows through `translation_parent_id` to the matching English narrative.
- Linked extra variants through `paraphrase_parent_id` to the matching English narrative.
- Marked all new rows as `source_type=synthetic_pending_review`, `annotation_status=pending_review`, and left `language_reviewer_id` blank.

## Validation
- Total rows: 1,500.
- Languages: 750 English, 600 Hindi, 150 Hindi-Latin.
- Duplicate `narrative_id`: 0.
- Invalid `scenario_id` references: 0.
- Missing Devanagari Hindi scenario coverage: 0.
- Invalid `translation_parent_id` references: 0.
- Invalid `paraphrase_parent_id` references: 0.
- Synthetic rows missing scenario date/time anchors: 0.

## Important Follow-Up
`classifications.csv` still has 600 rows, so the 900 new narratives do not yet have one classification each. That should be the next cascade step if the dataset contract requires one classification per narrative.
