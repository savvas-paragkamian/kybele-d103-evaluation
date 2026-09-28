import csv, json, re, string, collections
exec(open('curation2.py').read())
T={}
for l in open('treatments.jsonl',encoding='utf-8'):
    d=json.loads(l); T[d['docid']]=d
ws=lambda t: re.sub(r'\s+',' ',t or '').strip()
old=list(csv.DictReader(open('benchmark.csv',encoding='utf-8')))          # 139 curated (general)
oldcand={r['qid']:r for r in csv.DictReader(open('candidates_curated.csv',encoding='utf-8'))}
new=list(csv.DictReader(open('new_candidates_raw.csv',encoding='utf-8')))
TPL={'body_size':re.compile(r"^What is the body length of .+\?$"),'habitat':re.compile(r"^What is the habitat of .+\?$"),'trophic_guild':re.compile(r"^What does .+ feed on\?$")}
QT={'body_length':'body_size','habitat':'habitat'}
FAM=["Hypogastruridae","Neanuridae","Onychiuridae","Tullbergiidae","Odontellidae","Brachystomellidae","Poduridae","Isotomidae","Entomobryidae","Orchesellidae","Lepidocyrtidae","Paronellidae","Cyphoderidae","Tomoceridae","Oncopoduridae","Isotogastruridae","Sminthuridae","Katiannidae","Dicyrtomidae","Bourletiellidae","Sminthurididae","Arrhopalitidae","Neelidae","Mackenziellidae","Coenaletidae"]
def fam(d):
    c=collections.Counter(f for f in FAM for _ in re.finditer(f, d['article_title']+' '+d['text']))
    return c.most_common(1)[0][0] if c else 'unassigned'
def locate(text, gold):
    for a in [g.strip() for g in gold.split('||')]:
        i=text.find(a)
        if i<0: i=text.lower().find(a.lower())
        if i>=0: return i, len(a)
    return -1, 0
bench=[]; cand=[]
excluded=[]
for r in old:
    qt=QT.get(r['question_type'])
    if not qt: continue
    if not TPL[qt].match(r['question']): excluded.append((r['qid'],r['question'])); continue
    r2=dict(r); r2['question_type']=qt; bench.append(r2)
    c=dict(oldcand[r['qid']]); c['question_type']=qt; cand.append(c)
used_sp={b['taxon'].lower() for b in bench}
for r in new:
    c=C2.get(r['qid'])
    if not c or c['action']=='drop': continue
    d=T[r['docid']]; text=ws(d['text']); off,ln=locate(text,c['gold'])
    ctx=text[max(0,off-300):off+ln+300] if off>=0 else r['gold_context']
    b={'qid':r['qid'],'docid':r['docid'],'taxon':r['species'],'family':r['family'],'question_type':r['question_type'],
       'question':r['question'],'gold_answer':c['gold'],'gold_context':ctx,'answer_offset':off,'text_length':len(text),
       'treatment_title':r['treatment_title'],'article_title':r['article_title'],'doi':r['doi'],'treatment_uri':r['treatment_uri'],'curation_note':c['note']}
    bench.append(b)
    cand.append({**{k:r[k] for k in ['qid','docid','species','treatment_title','family','article_title','doi','treatment_uri','question_type','question']},
                 'candidate_answer':c['gold'].split('||')[0].strip(),'gold_context':ctx,'answer_offset':off,'text_length':len(text),'gold_answer':c['gold'],'curation':'new','curation_note':c['note']})
# Neelus koseli (diet from gut contents)
nk=[d for d in T.values() if d['treatment_title'].startswith('Neelus koseli')][0]
text=ws(nk['text']); g="clay and organic particles || fungal hyphae || fungal spores"; off,ln=locate(text,g)
q={'qid':'K248','docid':nk['docid'],'taxon':'Neelus koseli','family':fam(nk),'question_type':'trophic_guild','question':'What does Neelus koseli feed on?',
   'gold_answer':g,'gold_context':text[max(0,off-300):off+ln+300],'answer_offset':off,'text_length':len(text),'treatment_title':nk['treatment_title'],
   'article_title':nk['article_title'],'doi':nk['doi'],'treatment_uri':nk['treatment_uri'],'curation_note':'gut contents: clay and organic particles, fungal hyphae, fungal spores'}
bench.append(q)
cand.append({'qid':'K248','docid':nk['docid'],'species':'Neelus koseli','treatment_title':nk['treatment_title'],'family':q['family'],'article_title':nk['article_title'],'doi':nk['doi'],'treatment_uri':nk['treatment_uri'],'question_type':'trophic_guild','question':q['question'],'candidate_answer':'clay and organic particles','gold_context':q['gold_context'],'answer_offset':off,'text_length':len(text),'gold_answer':g,'curation':'new','curation_note':q['curation_note']})
print('excluded non-template:',excluded)
print('Neelus koseli already used:', 'neelus koseli' in used_sp)
# checks
def norm(t): t=t.lower().translate(str.maketrans('','',string.punctuation+'–—‘’“”')); return ' '.join(t.split())
bad=[(b['qid'],a.strip()) for b in bench for a in b['gold_answer'].split('||') if norm(a) not in norm(T[b['docid']]['text'])]
print('gold alternatives not verbatim:',bad)
ids=[b['qid'] for b in bench]; print('duplicate qids:', [i for i,c in collections.Counter(ids).items() if c>1])
sp=collections.Counter(b['taxon'].lower() for b in bench); print('species repeated:', [s for s,c in sp.items() if c>1])
print(len(bench), collections.Counter(b['question_type'] for b in bench))
print('families:', len(set(b['family'] for b in bench)), collections.Counter(b['family'] for b in bench).most_common(4))
offs=[int(b['answer_offset']) for b in bench]; print('not located',sum(o<0 for o in offs),'>600',sum(o>600 for o in offs),'>1500',sum(o>1500 for o in offs))
bf=['qid','docid','taxon','family','question_type','question','gold_answer','gold_context','answer_offset','text_length','treatment_title','article_title','doi','treatment_uri','curation_note']
with open('benchmark_traits.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=bf,extrasaction='ignore'); w.writeheader(); w.writerows(bench)
cf=list(cand[0].keys())
for c in cand:
    for k in cf: c.setdefault(k,'')
with open('/home/claude/kybele_eval/candidates.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cf,extrasaction='ignore'); w.writeheader(); w.writerows(cand)
print('candidates for runner:', len(cand))
