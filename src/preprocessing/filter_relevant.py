import os
import re

SEGMENTED_DIR = "../../Data/Segmented Data/BBC News TV/2019"
FILTERED_DIR = "../../Data/Filtered Data/BBC News TV/2019"

os.makedirs(FILTERED_DIR, exist_ok=True)

COVID_TERMS = [
    "covid", "covid-19", "coronavirus", "sars-cov-2", "pandemic", "epidemic",
    "outbreak", "virus", "viral", "infection", "infectious",
    "vaccine", "vaccination", "jab", "booster", "dose", "immunity", "immune",
    "antibody", "antibodies", "variant", "strain", "mutation",
    "testing", "test", "pcr", "lateral flow", "antigen",
    "positive", "negative", "cases", "case numbers", "deaths", "fatalities",
    "mortality", "hospitalisations", "icu", "ventilator", "oxygen",
    "symptoms", "long covid",
    "lockdown", "restrictions", "measures", "rules", "guidelines", "tiers",
    "stay-at-home", "curfew", "quarantine", "isolation", "shielding",
    "social distancing", "distancing", "mask", "face mask", "ppe",
    "travel ban", "border controls", "closures", "reopening",
    "nhs", "health service", "public health", "who",
    "world health organisation", "cdc", "government advice",
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

for filename in os.listdir(SEGMENTED_DIR):
    if not filename.lower().endswith(".txt"):
        continue

    with open(os.path.join(SEGMENTED_DIR, filename), "r", encoding="utf-8") as f:
        sentences = f.readlines()

    relevant = [s.strip() for s in sentences if COVID_REGEX.search(s)]

    if not relevant:
        continue

    with open(os.path.join(FILTERED_DIR, filename), "w", encoding="utf-8") as f:
        for sentence in relevant:
            f.write(sentence + "\n")
