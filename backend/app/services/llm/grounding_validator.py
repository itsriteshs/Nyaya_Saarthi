"""Conservative structural gate; a passing result is not a legal verification."""
import re

URL = re.compile(r"https?://|www\.", re.I)
MONEY = re.compile(r"(?:₹|rs\.?|inr|rupees?|fine of|penalty of|जुर्माना|रुपये)\s*[\d,]+|[\d,]+\s*(?:rupees?|inr|रुपये)", re.I)
DEADLINE = re.compile(r"\b\d+\s*(?:days?|weeks?|months?|years?|घंटे|दिन|हफ्ते|महीने)\b", re.I)
SPEED = re.compile(r"\b\d+\s*(?:km\s*/\s*h|kmph|kph|किमी\s*/\s*घंटा)", re.I)
SECTION = re.compile(r"\b(?:section|sec\.?|धारा|rule)\s*\d+[A-Za-z]*(?:\(\d+\))*", re.I)
OUTCOME = re.compile(r"\b(?:you (?:will|must) (?:be fined|pay|be convicted)|definitely (?:illegal|guilty|liable)|fine is|penalty is|you violated)\b|(?:निश्चित रूप से|पक्का)\s*(?:दोषी|अवैध|जुर्माना)", re.I)


def validate(output, package):
    reasons = []
    ids = {e["evidenceId"] for e in package["evidence"]}
    used = {ref for claim in output.legalClaims for ref in claim.evidenceIds}
    if not ids or not output.legalClaims:
        reasons.append("INSUFFICIENT_CITED_EVIDENCE")
    if used - ids:
        reasons.append("UNKNOWN_EVIDENCE_ID")
    full = " ".join([output.answer, output.explanation] + [c.text for c in output.legalClaims]
                    + output.uncertainties + output.recommendedActions)
    if URL.search(full): reasons.append("MODEL_URL_DISALLOWED")
    # No numeric penalty, deadline, or speed threshold is eligible in the current dataset.
    if MONEY.search(full): reasons.append("UNSUPPORTED_PENALTY")
    if DEADLINE.search(full): reasons.append("UNSUPPORTED_DEADLINE")
    if SPEED.search(full): reasons.append("UNSUPPORTED_SPEED_FIGURE")
    allowed_sections = {s.lower() for e in package["evidence"] for s in SECTION.findall(e["provision"] + " " + e["passage"])}
    if any(section.lower() not in allowed_sections for section in SECTION.findall(full)):
        reasons.append("UNKNOWN_SECTION")
    # Exact server-authored limitations are already trusted uncertainty, not a
    # model assertion of liability. E.g. "no ... penalty is asserted" previously
    # matched "penalty is". All generated prose/actions/claims and every changed
    # uncertainty still pass the unchanged outcome gate; numeric gates above
    # continue to examine the entire output.
    outcome_text = ' '.join([output.answer, output.explanation] + [c.text for c in output.legalClaims]
                            + output.recommendedActions + [u for u in output.uncertainties
                                if u not in package.get('uncertainties', [])])
    if OUTCOME.search(outcome_text): reasons.append("DEFINITE_OUTCOME")
    if package.get('uncertainties') and not output.uncertainties:
        reasons.append('OMITTED_UNCERTAINTY')
    titles = {step["title"] for step in package["supportedActions"]}
    omitted_actions = [action for action in output.recommendedActions if action not in titles]
    # Deterministic limitations are appended server-side and cannot be deleted
    # by an incomplete or translated model uncertainty list.
    for claim in output.legalClaims:
        if claim.text not in output.answer and claim.text not in output.explanation:
            reasons.append("UNLINKED_CLAIM")
        if not claim.evidenceIds or any(ref not in ids for ref in claim.evidenceIds):
            reasons.append("CLAIM_CITATION_INVALID")
    return {"accepted": not reasons, "reasonCodes": sorted(set(reasons)),
            "warningCodes": ["UNSUPPORTED_ACTION_OMITTED"] if omitted_actions else [],
            "omittedActions": omitted_actions,
            "unsupportedCitations": sorted(used - ids), "fallbackRequired": bool(reasons)}
