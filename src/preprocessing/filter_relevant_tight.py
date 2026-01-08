import os
import re

SEGMENTED_DIR = "../../data/segmented/BBC News TV"
FILTERED_DIR = "../../data/filtered/tight/BBC News TV"

os.makedirs(FILTERED_DIR, exist_ok=True)

# Direct terms - only need 1 match
DIRECT_TERMS = [
    "covid", "covid-19", "coronavirus", "sars-cov-2"
]

# Indirect terms - need 2+ matches
INDIRECT_TERMS = [
    "pandemic", "epidemic",
    "outbreak", "virus", "viral", "infection", "infectious",
    "vaccine", "vaccination", "jab", "booster", "dose", "immunity", "immune",
    "antibody", "antibodies", "variant", "strain", "mutation",
    "alpha", "beta", "delta", "omicron", "epsilon",
    "testing", "test", "pcr", "lateral flow", "antigen",
    "positive", "negative", "cases", "case numbers", "deaths", "fatalities",
    "mortality", "hospitalisations", "hospital", "ventilator", "oxygen",
    "symptoms", "long covid", "fever", "cough", "breathlessness", "fatigue",
    "loss of taste", "loss of smell",
    "lockdown", "restrictions", "measures", "rules", "guidelines", "tiers",
    "stay-at-home", "stay at home", "curfew", "quarantine", "isolation", "shielding",
    "social distancing", "distancing", "mask", "face mask", "ppe",
    "travel ban", "border controls", "closures", "reopening",
    "nhs", "health service", "public health",
    "world health organisation", "national health service", "government advice",
    "scientists", "medical experts", "chief medical officer",
    "key workers", "frontline", "care homes", "nursing homes",
    "schools closure", "remote learning", "work from home", "furlough",
    "economic impact", "business closures", "supply chain",
    "first wave", "second wave", "third wave", "surge", "peak",
    "decline", "recovery", "post-pandemic"
]

DIRECT_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in DIRECT_TERMS) + r")\b",
    re.IGNORECASE
)

INDIRECT_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in INDIRECT_TERMS) + r")\b",
    re.IGNORECASE
)


def is_covid_relevant(sentence):
    """Check if sentence passes the filter criteria."""
    # If any direct term is found, sentence passes
    if DIRECT_REGEX.search(sentence):
        return True
    
    # Otherwise, need 2+ indirect terms
    indirect_matches = INDIRECT_REGEX.findall(sentence)
    return len(indirect_matches) >= 2


for root, _, files in os.walk(SEGMENTED_DIR):
    for filename in files:
        if not filename.lower().endswith(".txt"):
            continue

        input_path = os.path.join(root, filename)

        rel_dir = os.path.relpath(root, SEGMENTED_DIR)
        output_dir = os.path.join(FILTERED_DIR, rel_dir)
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)

        with open(input_path, "r", encoding="utf-8") as f:
            sentences = f.readlines()

        relevant = [s.strip() for s in sentences if is_covid_relevant(s)]

        if not relevant:
            continue

        with open(output_path, "w", encoding="utf-8") as f:
            for sentence in relevant:
                f.write(sentence + "\n")