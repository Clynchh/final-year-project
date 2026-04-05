# Shared COVID-related term lists used by the filtering scripts.
# DIRECT_TERMS: strong identifiers — one match is sufficient.
# INDIRECT_TERMS: contextual terms — require 2+ matches (tight filter) or 1+ (loose filter).
# COVID_TERMS: union of both lists, used by the loose filter.

DIRECT_TERMS = [
    "covid", "covid-19", "coronavirus", "sars-cov-2"
]

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
    "decline", "recovery", "post-pandemic",
]

COVID_TERMS = DIRECT_TERMS + INDIRECT_TERMS
