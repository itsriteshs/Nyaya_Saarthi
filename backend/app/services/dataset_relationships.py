"""Observed ID relationships. Columns omitted here are descriptive, not assumed FKs."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Relationship:
    source: str
    column: str
    target: str
    target_id: str
    optional: bool = True
    encoding: str = "auto"  # auto accepts one ID, |, ;, or JSON array

RELATIONSHIPS = [
    Relationship("legal_provisions.csv", "source_id", "legal_sources.csv", "source_id", False),
    Relationship("legal_provisions.csv", "jurisdiction_id", "jurisdictions.csv", "jurisdiction_id", False),
    Relationship("legal_provisions.csv", "supersedes_provision_id", "legal_provisions.csv", "provision_id"),
    Relationship("legal_sources.csv", "jurisdiction_id", "jurisdictions.csv", "jurisdiction_id", False),
    Relationship("legal_sources.csv", "supersedes_source_id", "legal_sources.csv", "source_id"),
    Relationship("rule_logic.csv", "provision_id", "legal_provisions.csv", "provision_id", False),
    Relationship("rule_logic.csv", "jurisdiction_id", "jurisdictions.csv", "jurisdiction_id", False),
    Relationship("rule_logic.csv", "vehicle_class_id", "vehicle_classes.csv", "vehicle_class_id"),
    Relationship("rule_logic.csv", "required_slot_ids", "slot_schema.csv", "slot_name"),
    Relationship("rule_logic.csv", "optional_slot_ids", "slot_schema.csv", "slot_name"),
    Relationship("offences_penalties.csv", "provision_id", "legal_provisions.csv", "provision_id", False),
    Relationship("offences_penalties.csv", "source_id", "legal_sources.csv", "source_id", False),
    Relationship("offences_penalties.csv", "state_notification_source_id", "legal_sources.csv", "source_id"),
    Relationship("offences_penalties.csv", "vehicle_class_id", "vehicle_classes.csv", "vehicle_class_id"),
    Relationship("procedure_steps.csv", "procedure_id", "procedures.csv", "procedure_id", False),
    Relationship("procedure_steps.csv", "required_document_ids", "document_requirements.csv", "requirement_id"),
    Relationship("procedure_steps.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("procedures.csv", "official_service_id", "official_services.csv", "service_id"),
    Relationship("procedures.csv", "required_document_ids", "document_requirements.csv", "requirement_id"),
    Relationship("procedures.csv", "required_form_ids", "official_forms.csv", "form_id"),
    Relationship("procedures.csv", "legal_basis_provision_ids", "legal_provisions.csv", "provision_id"),
    Relationship("procedures.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("document_requirements.csv", "form_ids", "official_forms.csv", "form_id"),
    Relationship("document_requirements.csv", "procedure_id", "procedures.csv", "procedure_id"),
    Relationship("document_requirements.csv", "provision_id", "legal_provisions.csv", "provision_id"),
    Relationship("document_requirements.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("accident_relief_and_claims.csv", "required_document_ids", "document_requirements.csv", "requirement_id"),
    Relationship("accident_relief_and_claims.csv", "procedure_id", "procedures.csv", "procedure_id"),
    Relationship("accident_relief_and_claims.csv", "provision_id", "legal_provisions.csv", "provision_id"),
    Relationship("accident_relief_and_claims.csv", "scheme_source_id", "legal_sources.csv", "source_id"),
    Relationship("case_law_interpretations.csv", "provision_ids", "legal_provisions.csv", "provision_id"),
    Relationship("plain_language_multilingual.csv", "provision_id", "legal_provisions.csv", "provision_id", False),
    Relationship("plain_language_multilingual.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("speed_limits.csv", "jurisdiction_id", "jurisdictions.csv", "jurisdiction_id", False),
    Relationship("speed_limits.csv", "vehicle_class_id", "vehicle_classes.csv", "vehicle_class_id", False),
    Relationship("speed_limits.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("vehicle_classes.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("vehicle_classes.csv", "provision_id", "legal_provisions.csv", "provision_id"),
    Relationship("slot_schema.csv", "intent_id", "intents.csv", "intent_id", False),
    Relationship("intents.csv", "parent_intent_id", "intents.csv", "intent_id"),
    Relationship("intents.csv", "default_required_slot_ids", "slot_schema.csv", "slot_name"),
    Relationship("intents.csv", "conditional_slot_ids", "slot_schema.csv", "slot_name"),
    Relationship("intents.csv", "relevant_rule_ids", "rule_logic.csv", "rule_id"),
    Relationship("intents.csv", "relevant_procedure_ids", "procedures.csv", "procedure_id"),
    Relationship("query_provision_relevance.csv", "query_id", "annotated_utterances.csv", "utterance_id", False),
    Relationship("query_provision_relevance.csv", "intent_id", "intents.csv", "intent_id", False),
    Relationship("query_provision_relevance.csv", "provision_id", "legal_provisions.csv", "provision_id", False),
    Relationship("query_provision_relevance.csv", "source_id", "legal_sources.csv", "source_id"),
    Relationship("gold_evaluation_cases.csv", "expected_primary_intent", "intents.csv", "intent_id"),
    Relationship("gold_evaluation_cases.csv", "expected_rule_ids", "rule_logic.csv", "rule_id"),
    Relationship("gold_evaluation_cases.csv", "expected_provision_ids", "legal_provisions.csv", "provision_id"),
    Relationship("gold_evaluation_cases.csv", "expected_penalty_record_ids", "offences_penalties.csv", "offence_id"),
    Relationship("gold_evaluation_cases.csv", "expected_procedure_ids", "procedures.csv", "procedure_id"),
    Relationship("gold_evaluation_cases.csv", "expected_source_ids", "legal_sources.csv", "source_id"),
    Relationship("adaptive_conversations.jsonl", "primary_intent_id", "intents.csv", "intent_id"),
    Relationship("adaptive_conversations.jsonl", "ground_truth_rule_ids", "rule_logic.csv", "rule_id"),
    Relationship("adaptive_conversations.jsonl", "ground_truth_provision_ids", "legal_provisions.csv", "provision_id"),
    Relationship("adaptive_conversations.jsonl", "expected_procedure_ids", "procedures.csv", "procedure_id"),
]
