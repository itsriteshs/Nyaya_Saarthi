import { defaultSituation } from "@/data/examples";
import type { MockNlpResult, NlpFact } from "@/types/nlp";

// Frontend prototype only.
// Real NLP results will come from the FastAPI backend.
export function analyzeSituation(input: string): MockNlpResult {
  const inputText = input.trim() || defaultSituation;
  const lower = inputText.toLowerCase();

  const issue = detectIssue(lower);
  const speed = extractSpeed(inputText, lower);
  const vehicle = extractVehicle(lower);
  const location = extractLocation(inputText, lower);
  const authority = extractAuthority(lower);
  const challan = extractChallanStatus(lower);
  const document = extractDocument(lower);

  const extractedFacts: NlpFact[] = [];

  if (speed) {
    extractedFacts.push({ label: "Speed", value: speed, source: "user" });
  }

  if (vehicle) {
    extractedFacts.push({ label: "Vehicle type", value: vehicle, source: "user" });
  }

  if (location) {
    extractedFacts.push({ label: "Location", value: location, source: "user" });
  }

  if (authority) {
    extractedFacts.push({ label: "Authority", value: authority, source: "user" });
  }

  if (challan) {
    extractedFacts.push({ label: "Challan status", value: challan, source: "user" });
  }

  if (document) {
    extractedFacts.push({ label: "Document mentioned", value: document, source: "user" });
  }

  if (lower.includes("expressway") && !location?.toLowerCase().includes("expressway")) {
    extractedFacts.push({
      label: "Road context",
      value: "Expressway mentioned",
      source: "inferred",
    });
  }

  const missingInformation = getMissingInformation(issue.label, {
    speed: Boolean(speed),
    vehicle: Boolean(vehicle),
    location: Boolean(location),
    authority: Boolean(authority),
    challan: Boolean(challan),
    document: Boolean(document),
    policeAction: lower.includes("took") || lower.includes("seized") || lower.includes("impound"),
    accidentDetails: lower.includes("injury") || lower.includes("damage") || lower.includes("hit"),
    insuranceDate: lower.includes("expired") || lower.includes("valid"),
    registrationContext:
      lower.includes("owner") || lower.includes("transfer") || lower.includes("second-hand"),
  });

  const total = 4;
  const found = Math.max(1, total - Math.min(missingInformation.length, total - 1));

  return {
    inputText,
    detectedIssue: issue,
    extractedFacts:
      extractedFacts.length > 0
        ? extractedFacts
        : [{ label: "User description", value: "Road or vehicle situation provided", source: "user" }],
    missingInformation,
    readiness: {
      found,
      total,
    },
    nextQuestion: buildNextQuestion(missingInformation[0]),
    visibleSignals: ["Issue type", "Key facts", "Missing details", "Next question"],
  };
}

function detectIssue(lower: string) {
  if (/(speed|fast|limit|doing|crossed|\b[6-9][0-9]\b|\b1[0-9]{2}\b)/.test(lower)) {
    return {
      label: "Speed or traffic enforcement",
      description: "The query appears to involve speed, road context or enforcement.",
    };
  }

  if (/(challan|ticket|fine|penalty)/.test(lower)) {
    return {
      label: "Challan or traffic penalty",
      description: "A notice, fine or enforcement record may need review.",
    };
  }

  if (/(licence|license|\bdl\b|seized|impound|took my)/.test(lower)) {
    return {
      label: "Licence or document action",
      description: "The situation may involve police handling of a driving document.",
    };
  }

  if (/(insurance|policy|insured|expired)/.test(lower)) {
    return {
      label: "Insurance validity",
      description: "Vehicle insurance status may affect the next legal step.",
    };
  }

  if (/(accident|hit|crash|damage|injury|left)/.test(lower)) {
    return {
      label: "Accident or hit-and-run context",
      description: "Safety, reporting and evidence details may matter.",
    };
  }

  if (/(rc|registration|owner|transfer|second-hand|seller)/.test(lower)) {
    return {
      label: "Registration or RC transfer",
      description: "Ownership and vehicle registration context may be incomplete.",
    };
  }

  return {
    label: "Motor Vehicle Law context",
    description: "The situation needs a few facts before guidance can be grounded.",
  };
}

function extractSpeed(inputText: string, lower: string) {
  const looksSpeedRelated = /(speed|fast|limit|doing|crossed|km|kph|kmph|fine|fined)/.test(lower);
  if (!looksSpeedRelated) {
    return null;
  }

  const matches = Array.from(inputText.matchAll(/\b(\d{2,3})\s*(?:km\s*\/?\s*h|kmph|kph)?\b/gi));
  const speedMatch = matches.find((match) => {
    const value = Number(match[1]);
    return value >= 30 && value <= 220;
  });

  return speedMatch ? `${speedMatch[1]} km/h` : null;
}

function extractVehicle(lower: string) {
  if (/\b(car|private car|sedan|suv)\b/.test(lower)) {
    return "Private car";
  }

  if (/\b(bike|motorcycle|scooter|two-wheeler)\b/.test(lower)) {
    return "Two-wheeler";
  }

  if (/\b(bus)\b/.test(lower)) {
    return "Bus";
  }

  if (/\b(truck|lorry|commercial)\b/.test(lower)) {
    return "Commercial vehicle";
  }

  return null;
}

function extractLocation(inputText: string, lower: string) {
  const knownLocations = [
    "Bengaluru-Mysuru Expressway",
    "Bangalore-Mysore Expressway",
    "Avinashi Road",
    "Coimbatore",
    "Delhi",
    "Mumbai",
    "Chennai",
  ];

  const known = knownLocations.find((location) => lower.includes(location.toLowerCase()));
  if (known) {
    return known;
  }

  const roadMatch = inputText.match(
    /\b(?:on|at|near|in)\s+([A-Z][A-Za-z]+(?:[-\s][A-Z][A-Za-z]+)*\s(?:Road|Expressway|Highway|Junction|Circle|Bypass))\b/,
  );

  return roadMatch?.[1] ?? null;
}

function extractAuthority(lower: string) {
  if (lower.includes("traffic police")) {
    return "Traffic police";
  }

  if (lower.includes("police")) {
    return "Police";
  }

  return null;
}

function extractChallanStatus(lower: string) {
  if (/\b(no|not|without)\b.{0,24}\bchallan\b/.test(lower)) {
    return "No challan reported";
  }

  if (lower.includes("challan")) {
    return "Challan mentioned";
  }

  if (/(fine|fined|penalty|ticket)/.test(lower)) {
    return "Fine or penalty mentioned";
  }

  return null;
}

function extractDocument(lower: string) {
  if (/(licence|license|\bdl\b)/.test(lower)) {
    return "Driving licence";
  }

  if (/(rc|registration)/.test(lower)) {
    return "Registration certificate";
  }

  if (/(insurance|policy)/.test(lower)) {
    return "Insurance";
  }

  return null;
}

function getMissingInformation(
  issue: string,
  found: {
    speed: boolean;
    vehicle: boolean;
    location: boolean;
    authority: boolean;
    challan: boolean;
    document: boolean;
    policeAction: boolean;
    accidentDetails: boolean;
    insuranceDate: boolean;
    registrationContext: boolean;
  },
) {
  if (issue.includes("Speed")) {
    return compactMissing([
      !found.speed && "Reported speed",
      !found.vehicle && "Vehicle type",
      !found.location && "Road or location",
      !found.challan && "Whether a challan was issued",
    ]);
  }

  if (issue.includes("Challan")) {
    return compactMissing([
      !found.challan && "Challan notice details",
      !found.vehicle && "Vehicle or registration details",
      !found.location && "Place of alleged offence",
      "Reason you believe it is wrong",
    ]);
  }

  if (issue.includes("Licence")) {
    return compactMissing([
      !found.policeAction && "What action police took",
      !found.authority && "Which authority interacted with you",
      !found.location && "Where this happened",
      "Whether written notice was given",
    ]);
  }

  if (issue.includes("Insurance")) {
    return compactMissing([
      !found.insuranceDate && "Insurance expiry or validity date",
      !found.vehicle && "Vehicle type",
      "Whether the vehicle is being driven now",
      "Policy or renewal status",
    ]);
  }

  if (issue.includes("Accident")) {
    return compactMissing([
      !found.accidentDetails && "Damage or injury details",
      !found.location && "Accident location",
      !found.vehicle && "Vehicle details",
      "Police or insurance reporting status",
    ]);
  }

  if (issue.includes("Registration")) {
    return compactMissing([
      !found.registrationContext && "Buyer and seller context",
      !found.vehicle && "Vehicle details",
      !found.document && "RC or registration details",
      "Date of purchase or transfer request",
    ]);
  }

  return ["Issue category", "Vehicle or document involved", "Location", "What outcome you need"];
}

function compactMissing(items: Array<string | false>) {
  return items.filter(Boolean) as string[];
}

function buildNextQuestion(firstMissing?: string) {
  switch (firstMissing) {
    case "Vehicle type":
    case "Vehicle or registration details":
    case "Vehicle details":
      return "What type of vehicle was involved?";
    case "Road or location":
    case "Place of alleged offence":
    case "Where this happened":
    case "Accident location":
    case "Location":
      return "Where did this happen?";
    case "Whether a challan was issued":
      return "Did you receive a challan or written notice?";
    case "Reported speed":
      return "What speed was recorded or alleged?";
    case "Insurance expiry or validity date":
      return "When did the insurance expire or renew?";
    default:
      return "What detail should NyayaSaarthi clarify first?";
  }
}
