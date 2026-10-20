# Archived generation failure audit

All 18 archived outputs were inspected. This is a replay, not a new inference evaluation. Semantic correctness and fluency have not received qualified review. Original failures retain their original statuses; stricter replay can reject previously accepted output.

| Model | Case | Requested language | Original disposition | Final replay reasons |
|---|---|---|---|---|
| llama3.2-3b | SYN_SPEED_01 | english | grounding_rejected | UNLINKED_CLAIM |
| llama3.2-3b | SYN_SPEED_01 | hindi | language_rejected | OUTPUT_LANGUAGE_MISMATCH, UNLINKED_CLAIM |
| llama3.2-3b | SYN_SPEED_01 | hinglish | grounding_rejected | OUTPUT_LANGUAGE_MISMATCH |
| llama3.2-3b | SYN_INSURANCE_01 | english | accepted | Passes structural gate; semantic support unreviewed |
| llama3.2-3b | SYN_INSURANCE_01 | hindi | language_rejected | OUTPUT_LANGUAGE_MISMATCH |
| llama3.2-3b | SYN_INSURANCE_01 | hinglish | accepted | OUTPUT_LANGUAGE_MISMATCH |
| llama3.2-3b | SYN_REGISTRATION_01 | english | grounding_rejected | UNLINKED_CLAIM |
| llama3.2-3b | SYN_REGISTRATION_01 | hindi | language_rejected | OUTPUT_LANGUAGE_MISMATCH |
| llama3.2-3b | SYN_REGISTRATION_01 | hinglish | accepted | OUTPUT_LANGUAGE_MISMATCH |
| mistral-7b | SYN_SPEED_01 | english | grounding_rejected | UNLINKED_CLAIM |
| mistral-7b | SYN_SPEED_01 | hindi | language_rejected | INSUFFICIENT_CITED_EVIDENCE, OUTPUT_LANGUAGE_MISMATCH |
| mistral-7b | SYN_SPEED_01 | hinglish | language_rejected | OUTPUT_LANGUAGE_MISMATCH, UNLINKED_CLAIM |
| mistral-7b | SYN_INSURANCE_01 | english | grounding_rejected | UNLINKED_CLAIM |
| mistral-7b | SYN_INSURANCE_01 | hindi | grounding_rejected | UNLINKED_CLAIM |
| mistral-7b | SYN_INSURANCE_01 | hinglish | language_rejected | OUTPUT_LANGUAGE_MISMATCH |
| mistral-7b | SYN_REGISTRATION_01 | english | grounding_rejected | UNLINKED_CLAIM |
| mistral-7b | SYN_REGISTRATION_01 | hindi | accepted | OUTPUT_LANGUAGE_MISMATCH |
| mistral-7b | SYN_REGISTRATION_01 | hinglish | language_rejected | OUTPUT_LANGUAGE_MISMATCH |

The original outcome flags on speed cases matched the phrase `penalty is` within a copied deterministic limitation. The precise matches and full raw generations are preserved in the referenced JSONL files. No citation-ID validity result is counted as independent legal support.

Category coverage: all archived JSON parsed and had required fields; all IDs were known; no numeric-claim rejection or runtime error was recorded. Every output has a complete parsed object; finish reasons were not recorded by the original adapter. Unsupported suggested actions were omitted. Language/claim-linkage failures and the false-positive outcome gate are the observed technical causes. Translation quality and omitted substantive exceptions cannot be certified by this audit.
