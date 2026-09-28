# Curation of trophic-guild items, harvest round 3 (v3 harvest + unreviewed pairs of rounds 1-2): T301-T392.
# Same conventions as curation_t1.py / curation_t2.py. Caps: <=6 documents per species (15 for F. candida),
# one question per (species, document), <=4 questions per document (the maximum already reached in round 1).
T3 = {}


def keep(tid, gold, guilds, evidence, hedged=False, note="", species=None):
    T3[tid] = dict(action="keep", gold=gold, guilds=guilds, evidence=evidence, hedged=hedged, note=note, species=species)


def drop(tid, note):
    T3[tid] = dict(action="drop", note=note)


keep("T303", "marine and terrestrial invertebrates, as well as marine macrophytes || marine and terrestrial invertebrates "
     "|| invertebrates || marine macrophytes", "predator|omnivore", "isotope",
     note="stable isotopes, gut content and literature combined")
keep("T305", "pepino || Solanum muricatum", "herbivore", "field", note="figure caption: feeding on pepino plants")
keep("T316", "seven saprophytic fungal species || saprophytic fungal species || fungi", "fungivore", "lab",
     note="food-preference and fitness experiment")
keep("T329", "preferred fungal species || fungal species || fungi", "fungivore", "literature",
     note="cites Scheu and Simmerling 2004")
keep("T335", "fungi without chemical defenses || fungi without repellant crystalline structures || modified A. nidulans "
     "|| fungi", "fungivore", "literature", note="review of mycophagy")
keep("T350", "fungi of different metal tolerance || fungi", "fungivore", "lab",
     note="comparative food-preference test; I. minor preferred metal-tolerant fungi less than F. fimetarioides")
keep("T362", "plant particles || plant-synthesised FAs and plant particles || plant material", "herbivore|detritivore", "gut",
     note="gut content and fatty-acid profile")
keep("T371", "fungivorous || fungi", "fungivore", "literature",
     note="label in the experimental design; same sentence as the kept S. curviseta item")
keep("T376", "Fusarium species || Fusarium", "fungivore", "literature")
keep("T304", "first order predator lifestyle || first order predator || predator || trophic level III", "predator", "isotope",
     note="document cap: <=4 questions per document")
keep("T325", "T. virens || Trichoderma virens || T. virens Gv29.8", "fungivore", "lab",
     note="choice experiments with T. virens")

REASONS = {
    "prey-of (the springtail is the food)": ["T301", "T313", "T336", "T337", "T341", "T345", "T347", "T358", "T359",
                                           "T370", "T388", "T389", "T391", "T392"],
    "table fragment": ["T306", "T310", "T311", "T312", "T315", "T340", "T349", "T352", "T353", "T380", "T386"],
    "toxicity-test or exposure diet, not natural diet": ["T318", "T319", "T320", "T324", "T326", "T327", "T328", "T331",
                                                        "T332", "T334", "T339", "T343", "T344", "T385", "T387"],
    "laboratory culture or stock food": ["T321", "T333", "T364", "T366", "T367", "T368", "T372", "T379"],
    "reference-list entry": ["T355", "T357", "T361", "T381"],
    "label only": ["T309", "T356", "T369", "T377", "T378", "T382", "T384"],
    "no diet statement or no food named": ["T302", "T308", "T314", "T322", "T342", "T346", "T348", "T351", "T360",
                                           "T363", "T373", "T374", "T375", "T390"],
    "incidental ingestion (plastic), not diet": ["T307"],
    "Medline or PMC copy of an item already in the benchmark": ["T338", "T354", "T365", "T383", "T323"],
    "redundant A. nidulans preference item for F. candida": ["T317", "T330"],
}
for why, tids in REASONS.items():
    for t in tids:
        drop(t, why)
