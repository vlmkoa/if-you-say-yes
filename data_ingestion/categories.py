"""
Category mapping for substances: used to categorize dashboard (Postgres) drugs and to resolve
opioids/benzo to TripSit canonical names in Neo4j. Keys are lowercased.
"""
from __future__ import annotations

# Canonical TripSit names for category-based lookup (must match combos.json keys)
TRIPSIT_OPIOIDS = "opioids"
TRIPSIT_BENZO = "benzodiazepines"

CATEGORIES = (
    "Stimulant",
    "Opioids",
    "Benzo",
    "Psychedelics",
    "Dissociative",
    "Alcohol",
    "Cannabinoid",
    "Depressant",
    "SSRI",
    "MAOI",
    "Other",
)

# name (lowercase) -> category. Research-based; extend as needed.
CATEGORY_BY_NAME: dict[str, str] = {}
for _name, _cat in [
    # Opioids
    ("heroin", "Opioids"),
    ("morphine", "Opioids"),
    ("oxycodone", "Opioids"),
    ("hydrocodone", "Opioids"),
    ("codeine", "Opioids"),
    ("fentanyl", "Opioids"),
    ("tramadol", "Opioids"),
    ("methadone", "Opioids"),
    ("buprenorphine", "Opioids"),
    ("opium", "Opioids"),
    ("oxycontin", "Opioids"),
    ("vicodin", "Opioids"),
    ("percocet", "Opioids"),
    # Benzo
    ("diazepam", "Benzo"),
    ("alprazolam", "Benzo"),
    ("clonazepam", "Benzo"),
    ("lorazepam", "Benzo"),
    ("xanax", "Benzo"),
    ("valium", "Benzo"),
    ("klonopin", "Benzo"),
    ("ativan", "Benzo"),
    ("temazepam", "Benzo"),
    ("bromazepam", "Benzo"),
    ("nitrazepam", "Benzo"),
    ("flunitrazepam", "Benzo"),
    ("chlordiazepoxide", "Benzo"),
    # Stimulants
    ("cocaine", "Stimulant"),
    ("amphetamine", "Stimulant"),
    ("amphetamines", "Stimulant"),
    ("methamphetamine", "Stimulant"),
    ("mdma", "Stimulant"),
    ("mda", "Stimulant"),
    ("caffeine", "Stimulant"),
    ("nicotine", "Stimulant"),
    ("methylphenidate", "Stimulant"),
    ("adderall", "Stimulant"),
    ("ritalin", "Stimulant"),
    ("4-fa", "Stimulant"),
    ("2-fa", "Stimulant"),
    ("3-fpm", "Stimulant"),
    ("a-pvp", "Stimulant"),
    ("a-php", "Stimulant"),
    ("mephedrone", "Stimulant"),
    ("modafinil", "Stimulant"),
    ("4-mmc", "Stimulant"),
    ("3-mmc", "Stimulant"),
    ("ethylone", "Stimulant"),
    ("butylone", "Stimulant"),
    ("pentylone", "Stimulant"),
    ("nep", "Stimulant"),
    ("hexen", "Stimulant"),
    ("4-cmc", "Stimulant"),
    ("3-cmc", "Stimulant"),
    ("adrafinil", "Stimulant"),
    ("armodafinil", "Stimulant"),
    ("phenibut", "Other"),
    # Psychedelics
    ("lsd", "Psychedelics"),
    ("psilocybin", "Psychedelics"),
    ("mushrooms", "Psychedelics"),
    ("dmt", "Psychedelics"),
    ("mescaline", "Psychedelics"),
    ("2c-b", "Psychedelics"),
    ("2c-i", "Psychedelics"),
    ("2c-e", "Psychedelics"),
    ("2c-t-2", "Psychedelics"),
    ("2c-t-7", "Psychedelics"),
    ("2c-t-x", "Psychedelics"),
    ("2c-x", "Psychedelics"),
    ("5-meo-dmt", "Psychedelics"),
    ("5-meo-mipt", "Psychedelics"),
    ("amt", "Psychedelics"),
    ("dox", "Psychedelics"),
    ("nbomes", "Psychedelics"),
    ("25i-nbome", "Psychedelics"),
    ("doc", "Psychedelics"),
    ("dom", "Psychedelics"),
    ("allylescaline", "Psychedelics"),
    ("proscaline", "Psychedelics"),
    ("4-aco-dmt", "Psychedelics"),
    ("4-ho-met", "Psychedelics"),
    ("4-ho-mipt", "Psychedelics"),
    ("4-aco-met", "Psychedelics"),
    ("4-aco-det", "Psychedelics"),
    ("1p-lsd", "Psychedelics"),
    ("1cp-lsd", "Psychedelics"),
    ("1b-lsd", "Psychedelics"),
    ("1v-lsd", "Psychedelics"),
    ("al-lad", "Psychedelics"),
    ("eth-lad", "Psychedelics"),
    ("ald-52", "Psychedelics"),
    ("25i-nbome", "Psychedelics"),
    ("25b-nbome", "Psychedelics"),
    ("25c-nbome", "Psychedelics"),
    ("25i-nboh", "Psychedelics"),
    ("25b-nboh", "Psychedelics"),
    ("2c-b-fly", "Psychedelics"),
    ("2c-c", "Psychedelics"),
    ("2c-d", "Psychedelics"),
    ("2c-p", "Psychedelics"),
    ("2c-t-21", "Psychedelics"),
    ("doc", "Psychedelics"),
    ("dom", "Psychedelics"),
    ("dob", "Psychedelics"),
    ("doi", "Psychedelics"),
    ("lsa", "Psychedelics"),
    ("1cp-mipla", "Psychedelics"),
    ("1cp-eth-lad", "Psychedelics"),
    ("5-meo-dalt", "Psychedelics"),
    ("5-meo-dipt", "Psychedelics"),
    ("dpt", "Psychedelics"),
    ("det", "Psychedelics"),
    ("dipt", "Psychedelics"),
    ("mipt", "Psychedelics"),
    ("met", "Psychedelics"),
    ("dalt", "Psychedelics"),
    # Dissociative
    ("ketamine", "Dissociative"),
    ("pcp", "Dissociative"),
    ("dextromethorphan", "Dissociative"),
    ("dxm", "Dissociative"),
    ("mxe", "Dissociative"),
    ("3-meo-pcp", "Dissociative"),
    ("3-ho-pcp", "Dissociative"),
    ("dck", "Dissociative"),
    ("2f-dck", "Dissociative"),
    ("2b-dck", "Dissociative"),
    ("nitrous", "Dissociative"),
    ("nitrous oxide", "Dissociative"),
    ("3-meo-pce", "Dissociative"),
    ("3-ho-pce", "Dissociative"),
    ("o-pce", "Dissociative"),
    ("methoxmetamine", "Dissociative"),
    ("3-meo-pcm", "Dissociative"),
    ("3-ho-pcm", "Dissociative"),
    # Alcohol & Depressants
    ("alcohol", "Alcohol"),
    ("ethanol", "Alcohol"),
    ("ghb", "Depressant"),
    ("gbl", "Depressant"),
    ("ghb/gbl", "Depressant"),
    ("baclofen", "Depressant"),
    # Cannabinoid
    ("cannabis", "Cannabinoid"),
    ("thc", "Cannabinoid"),
    ("cbd", "Cannabinoid"),
    ("marijuana", "Cannabinoid"),
    # SSRI / MAOI
    ("ssris", "SSRI"),
    ("fluoxetine", "SSRI"),
    ("sertraline", "SSRI"),
    ("citalopram", "SSRI"),
    ("escitalopram", "SSRI"),
    ("paroxetine", "SSRI"),
    ("maois", "MAOI"),
    ("phenelzine", "MAOI"),
    ("tranylcypromine", "MAOI"),
    ("moclobemide", "MAOI"),
    # TripSit canonical names (so they get a category when synced)
    ("opioids", "Opioids"),
    ("benzodiazepines", "Benzo"),
    ("lithium", "Other"),
]:
    CATEGORY_BY_NAME[_name.strip().lower()] = _cat


def get_category(name: str) -> str | None:
    """
    Return category for a substance name (case-insensitive).
    Uses explicit mapping first, then heuristic rules (substring/pattern) so more drugs get a category.
    """
    if not name or not isinstance(name, str):
        return None
    n = name.strip().lower()
    if n in CATEGORY_BY_NAME:
        return CATEGORY_BY_NAME[n]
    # Heuristic rules for names not in the explicit list (research-based patterns)
    if "opioid" in n or "morphin" in n or "fentanyl" in n or "codeine" in n or "oxycodone" in n or "heroin" in n or "tramadol" in n or "buprenorphine" in n or "methadone" in n or "pethidine" in n or "hydromorphone" in n or "tapentadol" in n or n == "odsmt" or "o-desmethyltramadol" in n:
        return "Opioids"
    if "benz" in n or "prazolam" in n or "zolam" in n or "zepam" in n or "etizolam" in n or "flunitraz" in n or "bromaz" in n or "diazepam" in n or "lorazepam" in n or "clonazepam" in n or "alprazolam" in n or "temazepam" in n or "midazolam" in n or "triazolam" in n:
        return "Benzo"
    if "lsd" in n or "lad" in n or "lyserg" in n or "ergoline" in n or "2c-" in n or "2c-" in n or "nbome" in n or "nboh" in n or "mescaline" in n or "psilocy" in n or "psilocin" in n or "dmt" in n or "dpt" in n or "det" in n or "dipt" in n or "mipt" in n or "met" in n or "5-meo" in n or "bufotenin" in n or "ayahuasca" in n or "allylescaline" in n or "proscaline" in n or "escaline" in n or "doc" == n or "dom" == n or "dob" in n or "doi" in n or "lsa" in n or "morning glory" in n or "tryptamine" in n or "phenethylamine" in n or "psychedelic" in n or "entheogen" in n:
        return "Psychedelics"
    if "ketamine" in n or "pcp" in n or "pce" in n or "pcm" in n or "dxm" in n or "dextromethorphan" in n or "mxe" in n or "methoxetamine" in n or "dissociative" in n or "arylcyclohexylamine" in n or "nitrous" in n or "diphenidine" in n or "ephenidine" in n:
        return "Dissociative"
    if "cannabis" in n or "cannabinoid" in n or "thc" in n or "cbd" in n or "jwh-" in n or "synthetic cannabinoid" in n or "ab-fubinaca" in n or "marijuana" in n:
        return "Cannabinoid"
    if "amphetamine" in n or "methamphetamine" in n or "cocaine" in n or "cathinone" in n or "mephedrone" in n or "mdma" in n or "mda" in n or "caffeine" in n or "methylphenidate" in n or "modafinil" in n or "stimulant" in n or "ephedrine" in n or "phenidate" in n or "a-pvp" in n or "a-php" in n or "4-fa" in n or "2-fa" in n or "3-fa" in n or "4-fma" in n or "ethylone" in n or "butylone" in n or "pentylone" in n or "hexedrone" in n or "nep" in n or "n ethyl" in n:
        return "Stimulant"
    if "ghb" in n or "gbl" in n or "baclofen" in n or "barbiturate" in n or "depressant" in n or "hypnotic" in n or "sedative" in n or "zolpidem" in n or "zopiclone" in n or "eszopiclone" in n or "methaqualone" in n:
        return "Depressant"
    if "ssri" in n or "fluoxetine" in n or "sertraline" in n or "citalopram" in n or "paroxetine" in n or "antidepressant" in n or "snri" in n:
        return "SSRI"
    if "maoi" in n or "mao-" in n or "phenelzine" in n or "tranylcypromine" in n or "moclobemide" in n or "rima" in n or "harmala" in n:
        return "MAOI"
    return None


def resolve_tripsit_lookup_name(name: str, category: str | None) -> str:
    """
    For interaction lookup: if category is Opioids return TRIPSIT_OPIOIDS,
    if Benzo return TRIPSIT_BENZO; else return lowercased name.
    """
    n = (name or "").strip().lower()
    if not n:
        return n
    if category == "Opioids":
        return TRIPSIT_OPIOIDS
    if category == "Benzo":
        return TRIPSIT_BENZO
    return n
