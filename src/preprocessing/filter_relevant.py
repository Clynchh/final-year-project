import os
import re

SEGMENTED_DIR = "../../data/segmented/BBC News TV"
FILTERED_DIR = "../../data/filtered/BBC News TV"

os.makedirs(FILTERED_DIR, exist_ok=True)

COVID_TERMS = [
    "covid", "covid-19", "coronavirus", "sars-cov-2", "pandemic", "epidemic",
    "outbreak", "virus", "viral", "infection", "infectious",
    "vaccine", "vaccination", "jab", "booster", "dose", "immunity", "immune",
    "antibody", "antibodies", "variant", "strain", "mutation",
    "alpha", "beta", "delta", "omicron", "epsilon",
    "testing", "test", "pcr", "lateral flow", "antigen",
    "positive", "negative", "cases", "case numbers", "deaths", "fatalities",
    "mortality", "hospitalisations", "hospital", "ventilator", "oxygen",
    "symptoms", "long covid",     "fever", "cough", "breathlessness", "fatigue",
    "loss of taste", "loss of smell",
    "lockdown", "restrictions", "measures", "rules", "guidelines", "tiers",
    "stay-at-home", "stay at home", "curfew", "quarantine", "isolation", "shielding",
    "social distancing", "distancing", "mask", "face mask", "ppe",
    "travel ban", "border controls", "closures", "reopening",
    "nhs", "health service", "public health",
    "world health organisation", "nhs", "national health service", "government advice",
    "scientists", "medical experts", "chief medical officer",
    "key workers", "frontline", "care homes", "nursing homes",
    "schools closure", "remote learning", "work from home", "furlough",
    "economic impact", "business closures", "supply chain",
    "first wave", "second wave", "third wave", "surge", "peak",
    "decline", "recovery", "post-pandemic", "living with covid"
]


COVID_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in COVID_TERMS) + r")\b",
    re.IGNORECASE
)

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

        relevant = [s.strip() for s in sentences if COVID_REGEX.search(s)]

        if not relevant:
            continue

        with open(output_path, "w", encoding="utf-8") as f:
            for sentence in relevant:
                f.write(sentence + "\n")
