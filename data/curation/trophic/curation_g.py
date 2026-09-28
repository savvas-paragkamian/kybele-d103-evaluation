# Curation of GENUS-level trophic items (harvest v4, genus level): G001-G050.
# Question: "What does {genus} feed on?" (the trait-mining pipeline's own question at genus level).
# Same criteria as the species rounds. A bare guild label counts when the document states it as the taxon's
# feeding mode (a description of the study organism, or a statement with a citation); labels that only name a
# role in an experimental food web, and epithets in passing, are dropped. Caps: <=6 documents per taxon,
# one question per (taxon, document), <=4 questions per document. sent = index of the sentence in review_g.json that holds the answer.
TG = {}


def keep(tid, gold, guilds, evidence, hedged=False, note="", sent=0):
    TG[tid] = dict(action="keep", gold=gold, guilds=guilds, evidence=evidence, hedged=hedged, note=note, sent=sent)


def drop(tid, note):
    TG[tid] = dict(action="drop", note=note)


keep("G001", "this biofilm || biofilm || diatoms", "algivore", "gut", hedged=True,
     note="'we assume ... have eaten this biofilm', gut content with diatoms")
keep("G012", "this biofilm || biofilm || diatoms", "algivore", "gut", hedged=True,
     note="same sentence as G001 (Agrenia and Desoria)")
keep("G005", "herbivorous || herbivore", "herbivore", "literature", note="guild stated about the genus, with citation")
keep("G038", "litter and some fungi || litter || fungi", "detritivore|fungivore", "literature")
keep("G009", "slime mold || slime molds", "fungivore", "lab",
     note="feeding observation (video); slime moulds scored as fungivory as in the expert review of Neanura muscorum")
keep("G014", "litter and its associated fungi and bacteria || litter || fungi and bacteria",
     "detritivore|fungivore|bacterivore", "literature")
keep("G015", "litter material and the adhering fungi and bacteria || litter material || fungi and bacteria",
     "detritivore|fungivore|bacterivore", "literature", note="one sentence classifying Entomobrya, Folsomia and Orchesella")
keep("G021", "litter material and the adhering fungi and bacteria || litter material || fungi and bacteria",
     "detritivore|fungivore|bacterivore", "literature")
keep("G033", "litter material and the adhering fungi and bacteria || litter material || fungi and bacteria",
     "detritivore|fungivore|bacterivore", "literature")
keep("G032", "the alga Pleurococcus || Pleurococcus || Desmococcus || alga", "algivore", "literature", sent=1,
     note="the alga most consumed in the natural habitat; also used as culture food")
keep("G024", "fungivores || fungi", "fungivore", "literature", hedged=True, note="'have been assumed to ... live as fungivores'")
keep("G042", "fungivores || fungi", "fungivore", "literature", hedged=True, note="same sentence as G024")
keep("G025", "microbivores || microbial", "microbivore", "isotope", hedged=True, sent=2)
keep("G043", "predator or scavenger || predator || scavenger || microbivores", "predator|detritivore|microbivore", "isotope",
     hedged=True, note="the paper suggests predator/scavenger in one place and microbivore in another")
keep("G031", "decomposers || first trophic level", "detritivore", "isotope")
keep("G045", "bacteria or bacterial feeding nematodes || bacteria || bacterial feeding nematodes", "bacterivore|predator",
     "field", hedged=True, note="density correlated with Gram-negative bacteria")
keep("G050", "bacteria or bacterial feeding nematodes || bacteria || bacterial feeding nematodes", "bacterivore|predator",
     "field", hedged=True, note="same sentence as G045")
keep("G047", "a variety of food materials including litter but also fungi and bacteria in the rhizosphere, algae as well as "
     "Nematoda || litter || fungi and bacteria || algae || Nematoda", "omnivore|detritivore|fungivore", "literature", sent=1)
keep("G049", "superficial molds and fine organic debris || molds || fine organic debris || fungivorous – detritivorous",
     "fungivore|detritivore", "literature", note="Plazi treatment: 'like other members of the genus Willowsia'")
keep("G027", "pollen", "herbivore", "literature",
     note="Plazi treatment citing Kevan & Kevan 1970 on Lepidocyrtus species; distinct from the L. chorus gut-content item")
keep("G040", "fungi || fungi-synthesised FAs and fungi in the gut", "fungivore", "gut",
     note="gut content and fatty acids; sentence continues in the context")

REASONS = {
    "prey-of (the springtail is the food)": ["G006", "G013", "G022", "G023", "G034", "G046"],
    "no diet statement or no food named": ["G002", "G003", "G004", "G008", "G010", "G011", "G020", "G026", "G029", "G030",
                                           "G037", "G044"],
    "table fragment": ["G017", "G019"],
    "species-level item (binomial with capital epithet), label only or figure caption": ["G016", "G018"],
    "laboratory culture food (yeast offered for filming)": ["G035"],
    "feeding deterrent, no diet statement": ["G036"],
    "label only, hedged": ["G048"],
    "Medline copy of PMC7934680": ["G041"],
    "isotope values only for this genus in this document": ["G007"],
    "same organism and experiment as a species-level item from this document": ["G028", "G039"],
}
for why, tids in REASONS.items():
    for t in tids:
        drop(t, why)
