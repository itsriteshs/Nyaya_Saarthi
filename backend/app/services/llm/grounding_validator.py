"""Conservative structural gate; a passing result is not a legal verification."""
import re

URL = re.compile(r"https?://|www\.", re.I)
MONEY = re.compile(r"(?:₹|rs\.?|inr|rupees?|fine of|penalty of|जुर्माना|रुपये)\s*[\d,]+|[\d,]+\s*(?:rupees?|inr|रुपये)", re.I)
DEADLINE = re.compile(r"\b\d+\s*(?:days?|weeks?|months?|years?|घंटे|दिन|हफ्ते|महीने)\b", re.I)
SPEED = re.compile(r"\b\d+\s*(?:km\s*/\s*h|kmph|kph|किमी\s*/\s*घंटा)", re.I)
SECTION = re.compile(r"\b(?:section|sec\.?|धारा|rule)\s*\d+\s*[A-Za-z]*(?:\s*\(\s*\d+\s*\))*", re.I)
OUTCOME = re.compile(r"\b(?:you (?:will|must) (?:be fined|pay|be convicted)|definitely (?:illegal|guilty|liable)|fine is|penalty is|you violated)\b|(?:निश्चित रूप से|पक्का)\s*(?:दोषी|अवैध|जुर्माना)", re.I)



def reported_speed_sentences(package):
    sentences=[]
    for fact in package.get('facts',[]):
        if fact['key']!='OBSERVED_SPEED' or not str(fact['value']).isdigit():continue
        unit=fact.get('unit')
        if unit!='km/h' and not (unit is None and SPEED.search(str(fact.get('sourceText','')))):continue
        value=fact['value']
        sentences.extend([f"You reported a speed of {value} km/h.", f"आपने अपनी गति {value} km/h बताई।", f"Aapne apni speed {value} km/h batayi."])
    return sentences


def _reported_speed_allowed(match, sentence, package):
    number=match.group(0).casefold()
    number=re.match(r'\d+',number).group(0)
    if re.search(r'\b(?:limit|maximum|permitted|legal|exceed|above|over|allowed|fine|penalty)\b|सीमा|से\s+अधिक',sentence,re.I):
        return False
    if not re.search(
            r'\b(?:you\s+(?:reported|said|stated|told\s+us|were\s+driving|were\s+traveling|were\s+travelling|drove|were\s+doing)|your\s+reported\s+speed|as\s+you\s+(?:reported|said|stated))\b'
            r'|आपने\s+(?:अपनी\s+गति|गति)\s*(?:बताई|कहा)|आप\s*\d+\s*(?:km\s*/\s*h|kmph|किमी\s*/\s*घंटा)\s*की\s*गति\s*से\s*(?:चला|चल)'
            r'|aapne\s+(?:apni\s+)?speed\s+(?:batayi|kahi)|aap\s+\d+\s*(?:km\s*/\s*h|kmph)\s+ki\s+speed\s+se\s+(?:drive|travel|chala)',
            sentence,re.I):
        return False
    return any(fact.get('key')=='OBSERVED_SPEED' and str(fact.get('value','')).isdigit()
               and str(fact['value'])==number and fact.get('unit')=='km/h'
               for fact in package.get('facts',[]))


def remove_reported_speed_fact_claims(output, package):
    """Keep a user-reported speed out of the legal-claim list and its citations."""
    retained=[]
    for claim in output.legalClaims:
        matches=list(SPEED.finditer(claim.text))
        if matches and all(_reported_speed_allowed(match,claim.text,package) for match in matches):
            continue
        retained.append(claim)
    output.legalClaims=retained


def _contains_claim_tokens(claim, text):
    claim_tokens=[m.group(0).casefold() for m in re.finditer(r'\w+',claim,re.UNICODE)]
    text_tokens=list(re.finditer(r'\w+',text,re.UNICODE))
    if not claim_tokens:return None
    tokens=[m.group(0).casefold() for m in text_tokens]
    for start in range(len(tokens)-len(claim_tokens)+1):
        if tokens[start:start+len(claim_tokens)]==claim_tokens:
            return text[text_tokens[start].start():text_tokens[start+len(claim_tokens)-1].end()]
    return None


def repair_claim_links(output):
    """Repair punctuation/whitespace-only claim copy differences, never paraphrases."""
    for claim in output.legalClaims:
        if claim.text in output.answer or claim.text in output.explanation:
            continue
        for text in (output.answer,output.explanation):
            span=_contains_claim_tokens(claim.text,text)
            if span:
                claim.text=span
                break


def _canonical_section(value):
    """Compare section citations independent of harmless spacing and script label."""
    match=SECTION.fullmatch(value.strip())
    if not match:return re.sub(r'\s+','',value).casefold()
    reference=re.sub(r'\s+','',match.group(0)).casefold()
    reference=re.sub(r'^(?:section|sec\.?|धारा|rule)','',reference)
    return reference

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
    prose=[output.answer,output.explanation]
    speed_invalid=False
    for text in prose:
        for match in SPEED.finditer(text):
            starts=[m.end() for m in re.finditer(r'[.!?।\n]\s*',text[:match.start()])]
            ends=[m.start() for m in re.finditer(r'[.!?।\n]',text[match.end():])]
            sentence=text[max(starts,default=0):match.end()+min(ends,default=len(text)-match.end())]
            if not _reported_speed_allowed(match,sentence,package):
                speed_invalid=True
    # Claims, actions and uncertainty never receive the reported-fact exemption.
    if any(SPEED.search(text) for text in [c.text for c in output.legalClaims]+output.uncertainties+output.recommendedActions):
        speed_invalid=True
    if speed_invalid: reasons.append("UNSUPPORTED_SPEED_FIGURE")
    allowed_sections = {_canonical_section(s) for e in package["evidence"] for s in SECTION.findall(e["provision"] + " " + e["passage"])}
    if any(_canonical_section(section) not in allowed_sections for section in SECTION.findall(full)):
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
