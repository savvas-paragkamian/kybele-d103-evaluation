# Curation decisions for the KYBELE D10.3 Collembola benchmark.
# action: keep (candidate as is), fix (edited question and/or gold), drop.
# gold: verbatim answer span(s) from the treatment; alternatives separated by " || " (any counts as correct).
# qtype: new question type when the question changes type.

C = {}

def keep(qid, gold=None, note=""):
    C[qid] = {"action": "keep" if gold is None else "fix", "gold": gold, "question": None, "qtype": None, "note": note}

def fix(qid, gold, question=None, qtype=None, note=""):
    C[qid] = {"action": "fix", "gold": gold, "question": question, "qtype": qtype, "note": note}

def drop(qid, note):
    C[qid] = {"action": "drop", "gold": None, "question": None, "qtype": None, "note": note}

# ---- K001-K025 ----
keep("K001", "0.88 mm || up to 0.88 mm")
fix("K002", "its distribution || China and Russia")
fix("K003", "oak leaf litter || in oak leaf litter and on the ground",
    question="What is the habitat of Ephemerotoma skarzynskii?", qtype="habitat",
    note="candidate span was not the type locality; habitat stated instead")
fix("K004", "Wanxian", question="What is the type locality of Folsomia wanxianensis?",
    note="span captured a heading; type locality given in etymology; name spelled as in text")
fix("K005", "1.0 mm || ~1.0 mm")
fix("K006", "Wanda M. Weiner", question="Who is Simonachorutes weinerae named after?",
    note="abbreviation cut the span")
fix("K007", "entrance and twilight zone of caves || caves || troglophilous")
drop("K008", "Niphargus is an amphipod, not Collembola (cave paper matched the search)")
fix("K009", "Brazil")
fix("K010", "a Cherokee word meaning “place (or land) of blue smoke” || place (or land) of blue smoke || Cherokee word")
fix("K011", "2.3 mm || up to 2.3 mm")
fix("K012", "550 µm || ~ 550 µm", question="What is the body length of Spinaethorax adamantis?",
    qtype="body_length", note="holotype depository not stated in this treatment; size given instead")
fix("K013", "Pulchauki, in Mahabarat range, near Godavari || Pulchauki")
fix("K014", "1.65 mm || 1.32 to 2.22 mm")
fix("K015", "the size of the sensilla in relation to ordinary chaetae || size of the sensilla")
fix("K016", "Dr. Jean-Marie Betsch || Jean-Marie Betsch", question="Who is Denisiella betschi named after?",
    note="treatment text has garbled capitalisation (OCR)")
fix("K017", "College of Plant Protection, Nanjing Agricultural University || Nanjing Agricultural University || NJAU")
keep("K018", "Northeastern and Central Brazil")
fix("K019", "on guano in the dark zone of a karstic cave || guano in the dark zone of a karstic cave || guano")
fix("K020", "Mary Fitzpatrick", question="Who is Katianna maryae named after?")
keep("K021", "under wet wood and in litter in deciduous forest")
fix("K022", "Shanghai Institute of Plant Physiology and Ecology, Shanghai Institutes for Biological Sciences, CAS || Shanghai Institute of Plant Physiology and Ecology")
fix("K023", "shores of Chocó, Colombia || Chocó, Colombia")
fix("K024", "humped || prominent Di tubercle of Abd. V")
fix("K025", "decomposing leaves along the roads")

# ---- K026-K050 ----
fix("K026", "1.9 mm || up to 1.9 mm")
fix("K027", "Northern Caucasus || Known only from the type locality in Northern Caucasus")
fix("K028", "Schmalhausen Institute of Zoology, National Academy of Sciences of Ukraine, Kyiv || Schmalhausen Institute of Zoology")
fix("K029", "1.0- 1.7mm || 1.0-1.7 mm || 1.0–1.7 mm")
fix("K030", "4.1–4.8mm || 4.1–4.8 mm || 4.1-4.8 mm")
fix("K031", "Vitim Plateau, vicinity of Telemba || Vitim Plateau || Telemba",
    note="candidate span was a remark on Kamchatka; type locality taken from the holotype record")
drop("K032", "Nevadesmus is a millipede, not Collembola")
fix("K033", "Yunnan Province, southeast China || Yunnan || Tibet",
    note="treatment adds a first record for Tibet")
fix("K034", "NHM-PSU")
fix("K035", "the commune of Calvignac || Calvignac")
fix("K036", "LBEA")
fix("K037", "dark zone of a cave on ground floor with small patch of bat guano || dark zone of a cave || bat guano")
fix("K038", "Tierra de Fuego, near Rio Grande, Argentina || Tierra de Fuego || Tierra del Fuego",
    note="candidate span was a comparison table; type locality taken from the holotype record")
fix("K039", "the mangrove of the genus Rhizophora || Rhizophora || mangrove",
    note="treatment text has garbled capitalisation (OCR)")
fix("K040", "MZNA")
drop("K041", "only antenna length is given, not body length")
fix("K042", "x") ; drop("K042", "Metagonia is a spider (Pholcidae), not Collembola")
fix("K043", "Pucarani-Condoriri, River Palcoco || Bolivia, Department of La Paz, Province Los Andes || River Palcoco")
fix("K044", "litter and soil mass of a coniferous forest dominated by the Korean pine || coniferous forest || Pinus koraiensis")
fix("K045", "Slovak and Aggtelek Karst || southern Slovakia and northeastern Hungary")
fix("K046", "Java, Samarang (= Semarang) || Samarang || Semarang",
    note="candidate span was a citation fragment")
fix("K047", "1.5 mm || up to 1.5 mm")
fix("K048", "South Australian Museum")
fix("K049", "about 1.2 mm || 1.23 mm || 1.2 mm", note="candidate span was male length; female/holotype length used")
fix("K050", "China: Zhejiang Province, Mountain Tiantong || Mountain Tiantong || Tiantong")

# ---- K051-K075 ----
fix("K051", "twilight zone of the cave || troglophilous")
fix("K052", "the Sayan Mountains in Southern Siberia || Sayan Mountains")
fix("K053", "associated to bushes || bushes")
keep("K054", "MZNA", note="span confirmed in full text: 'Holotype and 11 paratypes deposited in MZNA'")
fix("K055", "ICN / UNAL || ICN")
fix("K056", "Russia: Primorye: south of Posyet || south of Posyet || Primorye",
    note="candidate span was a DNA-barcode remark; type locality taken from the holotype record")
fix("K057", "its numerous sensilla on antennal segment IV || numerous sensilla")
fix("K058", "Eucalyptus plantations with a semiopen canopy || Eucalyptus plantations",
    note="candidate span cut at 'sp. nov.'")
fix("K059", "floating on water in a rock pool || rock pool", note="candidate span cut at 'sp. nov.'")
fix("K060", "Laboratorio de Artrópodos de suelo, Centro Internacional de Agricultura Tropical || Centro Internacional de Agricultura Tropical")
fix("K061", "Moghan Cave || Iran, Razavi Khorasan province, Mashhad city, Moghan village, Moghan Cave")
fix("K062", "Genista hispanica", question="From which plant was the holotype of Polydiscia deuterosminthurus collected?",
    qtype="habitat", note="candidate span was a heading; host plant from the type record")
fix("K063", "Songkhla", question="In which province was Cyphoderus songkhlaensis discovered?", qtype="type_locality",
    note="distribution only said 'type locality'; province from etymology")
fix("K064", "1.1–1.2 mm || 1.1-1.2 mm")
drop("K065", "Calima is a schizomid arachnid, not Collembola")
fix("K066", "Good’s biogeographic zone 27: South Brazilian || South Brazilian || Mangaratiba || Rio de Janeiro")
fix("K067", "the cold environment in which the species lives || cold environment")
keep("K068", "0.7 mm")
fix("K069", "2.3–3.4mm || 2.3–3.4 mm || 3.2mm || 3.2 mm")
fix("K070", "humus layer of mixed forest")
fix("K071", "Tuva || Tuva Republic", note="candidate span cut at 's.str.'")
fix("K072", "forest litter covering sandy soils in shady areas || forest litter || Atlantic Forest",
    note="candidate span cut at 'S.'")
fix("K073", "Motuo county || Motuo", question="What is the type locality of Metaphorura motuoensis?",
    qtype="type_locality", note="distribution only said 'type locality'; county from etymology")
fix("K074", "2.6 mm", question="What is the body length of Dicranocentrus icelosmarias?", qtype="body_length",
    note="candidate span was scale distribution on the body, not geography")
fix("K075", "Department of Zoology & Ecology, Moscow State Pedagogical University || Moscow State Pedagogical University")

# ---- K076-K100 ----
fix("K076", "Carpathian flower “chervona ruta” ( Rhododendron kotschyi ) || chervona ruta || Rhododendron kotschyi")
fix("K077", "the litter of montane deciduous forests || litter of montane deciduous forests")
keep("K078", "MNRJ")
fix("K079", "the Brazilian name for the northeastern semiarid vegetation || caatinga",
    note="treatment text has garbled capitalisation (OCR)")
fix("K080", "Pazariste cave in Yugoslavia || Pazariste cave", note="candidate span was the list of later records")
drop("K081", "Hyperglomeris is a pill millipede, not Collembola")
fix("K082", "1.1 mm || 1.0– 1.3 mm || 1.0-1.3 mm")
fix("K083", "Endemic to North America || North America")
fix("K084", "Duchesne, Utah || Duchesne", note="candidate span was the next sentence")
fix("K085", "soil inside cracks in rocks || soil under oak trees", note="first record and new Iranian record")
fix("K086", "Lancinha cave || Rio Branco do Sul, Lancinha cave", question="What is the type locality of Arrhopalites paranaensis?",
    qtype="type_locality", note="distribution gave only a biogeographic zone number")
fix("K087", "pasture fields || two different pasture fields")
fix("K088", "Prof. Mingyi Tian || Mingyi Tian", question="Who is Tomocerus tiani named after?",
    note="abbreviation 'Prof.' cut the span")
fix("K089", "MNSV")
fix("K090", "Nepal")
fix("K091", "the soil of a meadow in Hungary || soil of a meadow || leaf litter under oak trees")
fix("K092", "India: Terai Grassland, Valmiki Tiger Reserve || India || Nepal")
fix("K093", "anthropized environments || mostly found in anthropized environments")
fix("K094", "0.40–0.69 mm || 0.40-0.69 mm || 0.62 mm")
fix("K095", "‘arboreal’, which means ‘living in trees’ || living in trees || arboreal")
fix("K096", "Itatiaia municipality, Parque Nacional de Itatiaia || Parque Nacional de Itatiaia || Itatiaia")
fix("K097", "its type locality, Piaui State, Brazil || Piaui State || Piaui")
fix("K098", "Mrs. María Antònia Siquier || María Antònia Siquier", question="Who is Oncopodura siquierae dedicated to?",
    note="abbreviation 'Mrs.' cut the span")
fix("K099", "Hungarian Natural History Museum, Budapest || Hungarian Natural History Museum")
fix("K100", "Chassahowitzka National Wildlife Refuge in Citrus County, Florida || Florida || Endemic to North America")

# ---- K101-K125 ----
fix("K101", "1.5 mm || up to 1.5 mm")
fix("K102", "the foothills of Helan Mountain || Helan Mountain")
fix("K103", "Schmalhausen Institute of Zoology, NAS of Ukraine, Kiev || Schmalhausen Institute of Zoology")
fix("K104", "Costa Rica, Turrialba, forest close to CATIE || Turrialba || CATIE",
    note="treatment text has garbled capitalisation (OCR)")
fix("K105", "troglophilous || probably troglophilous species", note="only a general ecological statement is given")
fix("K106", "the Tuva Republic (Russian Federation) || Tuva Republic || Tuva")
drop("K107", "Palaeochiridium is a fossil pseudoscorpion in amber, not Collembola")
drop("K108", "Eupolybothrus is a centipede, not Collembola")
keep("K109", "Santa Cruz Island, Galapagos, Ecuador")
fix("K110", "Museum of New Zealand Te Papa Tongarewa, Wellington, New Zealand || Museum of New Zealand Te Papa Tongarewa || Te Papa")
fix("K111", "the high alpine zone where the species was found || high alpine zone")
fix("K112", "the old bark of the sago palm ( Metroxylon sagu Rottb ) at the lower trunk level || old bark of the sago palm || sago palm")
fix("K113", "0.88 mm || 0.47-1.20 mm")
fix("K114", "Laboratorio de Ecología y Sistemática de Microartrópodos, Sciences Faculty, UNAM, México || UNAM")
drop("K115", "Amelyris is a beetle (Melyridae), not Collembola")
fix("K116", "North America, Hawaii and possibly Europe || North America")
fix("K117", "1.5 mm || up to 1.5 mm")
fix("K118", "near Premier Resort Sani Pass || Sani Pass || KwaZulu-Natal", question="What is the type locality of Folsomotoma amyliuae?",
    qtype="type_locality", note="distribution only said 'type locality'; locality from the type record")
fix("K119", "0.7 mm || ~ 0.7 mm", note="length quoted from the original description")
fix("K120", "COLOMBIA: Cundinamarca province: Chingaza || Chingaza")
fix("K121", "3.5–4.0 mm || 3.5-4.0 mm")
keep("K122", "IGA-CAS")
fix("K123", "Robinia sp., shrubs, pines, and plant debris || Robinia || plant debris", note="span cut at 'sp.'")
fix("K124", "marine littoral sand")
fix("K125", "NHM-PSU")

# ---- K126-K150 ----
fix("K126", "Museo Nacional de Historia Natural de Chile, Santiago, Chile || Museo Nacional de Historia Natural de Chile")
fix("K127", "Argentina, Tierra del Fuego Province, near Rio Grande city || near Rio Grande city || Tierra del Fuego")
fix("K128", "deceitful || its similarity with D. inermodentes", note="span cut at 'D.'")
fix("K129", "0.45-0.95 mm", note="range of Brazilian specimens in a redescription")
fix("K130", "Piracuruca municipality, Piaui state, Brazil || Piracuruca")
fix("K131", "north-eastern Yakutia || Yakutia || Taimyr Peninsula", note="span cut at 'U.'")
fix("K132", "Tony Whitten", question="Who is Sinella whitteni named after?")
fix("K133", "East Kyzylkum sandy desert, basin of Syr Darya River, 85 km W of Arys || East Kyzylkum sandy desert || Kyzylkum",
    note="candidate span was a heading; locality from the holotype record")
fix("K134", "the late Tony Whitten || Tony Whitten", question="Who is Folsomides whitteni named after?")
keep("K135", "1.2 mm")
keep("K136", "0.84 mm")
fix("K137", "3.0 mm || up to 3.0 mm")
fix("K138", "broadleaved litter and soil, in an urban recreational park || urban recreational park || broadleaved litter and soil")
drop("K139", "Anillinus is a ground beetle, not Collembola")
fix("K140", "China (Xinjiang) || Xinjiang")
fix("K141", "Stefan M. Eberhard || Eberhard", question="Who is Troglopedetes eberhardi named after?",
    note="initial 'M.' cut the span")
fix("K142", "Senckenberg Museum für Naturkunde, Görlitz, Germany || Senckenberg Museum für Naturkunde")
fix("K143", "Ukraine, Eastern Carpathians, Chornochora Range, Pozhyzhevska Mt. || Pozhyzhevska Mt || Chornochora Range")
drop("K144", "Strumigenys is an ant, not Collembola")
fix("K145", "Endemic to North America || North America")
fix("K146", "Arne Fjellberg", question="Who is Xenylla arnei named after?")
fix("K147", "under leaf-litter of moist deciduous forest || leaf-litter of moist deciduous forest || Tussar plantation garden")
fix("K148", "a cave near the Buffalo River, in northern Arkansas || Buffalo River")
fix("K149", "leaf litter in deciduous forest")
fix("K150", "both twilight and dark zones of the cave || twilight and dark zones of the cave || troglophilous")
