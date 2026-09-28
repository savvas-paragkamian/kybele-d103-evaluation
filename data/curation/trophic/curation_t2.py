# Curation of trophic-guild items, harvest round 2 (T101-T137) and extra candidates (T201-T216).
# Same conventions as curation_t1.py. Species can be reassigned with species= when the sentence is about another species.
T2 = {}

def keep(tid, gold, guilds, evidence, hedged=False, note="", species=None):
    T2[tid] = dict(action="keep", gold=gold, guilds=guilds, evidence=evidence, hedged=hedged, note=note, species=species)

def drop(tid, note):
    T2[tid] = dict(action="drop", note=note)

for t, why in [("T101", "laboratory culture food"), ("T102", "prey-of"), ("T103", "table fragment"),
               ("T104", "laboratory culture food"), ("T105", "PMC copy of T006"), ("T106", "PMC copy of T010"),
               ("T108", "PMC copy of T012"), ("T109", "redundant Fusarium preference item"), ("T110", "table fragment"),
               ("T111", "redundant Fusarium preference item"), ("T113", "no diet statement"),
               ("T115", "hedged assumption for a group of genera"), ("T116", "reference-list entry"), ("T117", "prey-of"),
               ("T118", "isotope values only"), ("T119", "occurrence in litter is not diet"), ("T120", "occurrence in litter is not diet"),
               ("T121", "laboratory stock food"), ("T122", "the springtail is the food"), ("T123", "hedged, community-level"),
               ("T124", "Medline copy of T050"), ("T126", "reference-list entry"), ("T127", "reference-list entry"),
               ("T128", "statement about Collembola in general"), ("T129", "copy of T076"), ("T130", "PMC copy of T077"),
               ("T131", "third P. minuta item, redundant"), ("T132", "joint citation, redundant"), ("T133", "no diet statement"),
               ("T134", "label only"), ("T135", "habitat used to infer diet"), ("T136", "reference-list entry"),
               ("T137", "toxicity-test diet, not natural diet")]:
    drop(t, why)
keep("T107", "organic fertilizer", "detritivore", "lab")
keep("T112", "vegetative hyphae and conidia || A. nidulans || hyphae", "fungivore", "literature")
keep("T125", "U. isabellina || Umbelopsis isabellina", "fungivore", "literature", note="review of mycophagy")

keep("T201", "Phanerochaete velutina mycelial systems || Phanerochaete velutina || mycelial", "fungivore", "lab")
keep("T202", "the filamentous fungus Aspergillus nidulans || Aspergillus nidulans", "fungivore", "lab")
keep("T203", "S. perfoliatum litter || litter", "detritivore", "lab")
keep("T204", "the Streptomyces colonies || Streptomyces", "bacterivore", "lab")
keep("T205", "black fungi", "fungivore", "literature", hedged=True)
drop("T206", "table fragment")
keep("T207", "the external hyphae of AMF || hyphae of AMF || AMF", "fungivore", "literature")
drop("T208", "toxicity-test diet, not natural diet")
keep("T209", "fungi growing on organic surfaces || fungi", "fungivore", "literature")
drop("T210", "toxicity-test diet, not natural diet")
drop("T211", "generic label, redundant for F. candida")
drop("T212", "toxicity-test diet, not natural diet")
drop("T213", "redundant with T072")
drop("T214", "the springtail's egestions are the food")
keep("T215", "fine roots of Zea mays || fine roots || litter resources", "herbivore|detritivore", "literature",
     species="Protaphorura fimata", note="sentence states the diet switch for P. fimata")
keep("T216", "the fungal diet || fungal", "fungivore", "lab")
drop("T114", "laboratory culture food")
