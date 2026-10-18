"""Les 5 vidéos du soir refaites selon la feuille de route (accroche choc, 3 points, gag, question, abonnement)."""
import asyncio, json, os, sys
import make_tiktok as m, make_shorts as s, make_daily as dly

V = {  # index de scène -> contenu (faits tirés des titres de presse du 8 au 10 octobre 2026)
 2: dict(party='rn', slug='1-RN-dimanche-11', who='Gaspard le Chartreux · Sources : site du RN, Sud Ouest, Les Echos',
         hook=('Le RN recrute pour 2027 : ça change quoi ?', 'Gaspard t’explique, en soupirant'),
         text="Marine Le Pen muscle son équipe pour 2027. Gaspard soupire, mais il t'explique. Un : de nouveaux membres rejoignent son équipe de campagne, a annoncé le Rassemblement national sur son site. Deux : à l'Assemblée, le RN n'a pas réussi à faire adopter ses textes lors de sa niche parlementaire, selon Sud Ouest. Trois : sa proposition de taxe sur les salariés étrangers fait réagir les entreprises, d'après Les Echos. Moi aussi je recrute : quelqu'un pour me porter jusqu'à mon panier. Tu penses que ça va changer quelque chose ? Oui ou non ?",
         desc="Marine Le Pen recrute pour 2027 : ça change quoi ? 🐱🎤 Nouvelle équipe de campagne, échec du RN à l'Assemblée, taxe sur les salariés étrangers qui fait réagir : Gaspard le chartreux t'explique tout. Ça va changer quelque chose ? Oui ou non ? 👇\n#jtdeschatons #actu #politique #chaton #jt #marinelepen #rn #presidentielle2027"),
 3: dict(party='ren', slug='2-Renaissance-lundi-12', who='Mandarine la Maine Coon · Sources : France 3, Le Figaro, La Voix du Nord',
         hook=('Attal lance son pacte : bonne idée ?', 'Mandarine t’explique en vitesse'),
         text="Tu as compris quelque chose au pacte jeunesse de Gabriel Attal ? Mandarine fait vite, promis. Un : en meeting à Lyon samedi, le candidat Renaissance a présenté son pacte pour la jeunesse, selon France 3 Régions. Deux : Le Figaro parle aussi d'un nouveau pacte générationnel et d'une double règle d'or. Trois : la sénatrice Brigitte Bourguignon, ancienne ministre, quitte Renaissance, rapporte La Voix du Nord. Moi, mon pacte jeunesse, c'est trois siestes par jour, et je suis déjà en retard. Et toi, tu es pour ou contre ce pacte jeunesse ?",
         desc="Attal lance son pacte jeunesse : bonne idée ? 🐱🎤 Meeting à Lyon, double règle d'or, et Brigitte Bourguignon qui quitte Renaissance : Mandarine la Maine Coon t'explique en vitesse. Pour ou contre ? 👇\n#jtdeschatons #actu #politique #chaton #jt #attal #renaissance #pactejeunesse"),
 5: dict(party='eelv', slug='3-Ecologistes-mardi-13', who="Flocon l'Angora · Sources : franceinfo, La Voix du Nord, BFM",
         hook=('Les Écolos pressés pour 2027 ?', 'Flocon enquête (quand il est réveillé)'),
         text="Chez les Écologistes, on s'impatiente pour 2027. Flocon, réveille-toi, c'est à toi ! Un : Sandrine Rousseau appelle à accélérer la désignation pour la présidentielle, selon franceinfo. Deux : Marine Tondelier est allée à la rencontre de lycéens mobilisés dans un café de Douai, d'après La Voix du Nord. Trois : elle accuse le gouvernement de parier sur le pourrissement du mouvement lycéen, rapporte BFM. Pendant ce temps, moi, j'attends toujours que mes croquettes poussent dans la serre. Tu penses qu'ils doivent se dépêcher ? Oui ou non ?",
         desc="Les Écologistes pressés pour 2027 ? 🐱🎤 Sandrine Rousseau veut accélérer la désignation, Marine Tondelier rencontre les lycéens mobilisés : Flocon l'angora enquête. Ils doivent se dépêcher ? Oui ou non ? 👇\n#jtdeschatons #actu #politique #chaton #jt #lesecologistes #tondelier #presidentielle2027"),
 6: dict(party='lr', slug='4-LR-mercredi-14', who='Bjorn le Norvégien · Sources : Ouest-France, Le Monde, BFM',
         hook=('Retailleau veut refaire l’école : d’accord ?', 'Bjorn grogne, mais il t’explique'),
         text="Refaire toute l'école, rien que ça ? Bjorn grogne, mais il t'explique. Un : Bruno Retailleau, candidat à la présidentielle, veut une refonte complète du système éducatif, dans un entretien à Ouest-France. Deux : il reçoit le soutien de François Baroin, selon Le Monde. Trois : sur BFM, il désigne Jean-Luc Mélenchon comme son seul adversaire. Moi, la seule réforme que je demande, c'est la récré toute la journée. Et toi, tu es pour ou contre une refonte complète de l'école ?",
         desc="Retailleau veut refaire l'école : d'accord ? 🐱🎤 Refonte complète du système éducatif, soutien de François Baroin, Mélenchon désigné comme seul adversaire : Bjorn le norvégien t'explique. Pour ou contre ? 👇\n#jtdeschatons #actu #politique #chaton #jt #retailleau #lr #education"),
 1: dict(party='lfi', slug='5-LFI-jeudi-15', who='Pacha le Siamois · Sources : LCP, ici, Le Bien Public',
         hook=('LFI : salaires, pesticides, AESH !', 'Pacha est surexcité, accroche-toi'),
         text="Salaires, pesticides, AESH : c'est le menu de La France insoumise à l'Assemblée ! Pacha est surexcité, accroche-toi. Un : selon LCP, ce sont les textes que LFI défendra lors de sa niche parlementaire du 29 octobre. Deux : Jean-Luc Mélenchon, candidat à la présidentielle, était annoncé en meeting près de Clermont-Ferrand ce week-end, d'après ici. Trois : à Dijon, les députées Clémence Guetté et Aurélie Trouvé ont animé un meeting, rapporte Le Bien Public. Moi aussi j'ai une niche, et je ne la partage avec personne ! Et toi, tu es pour ou contre ces propositions ?",
         desc="LFI à l'Assemblée : salaires, pesticides, AESH ! 🐱🎤 Les textes de la niche parlementaire du 29 octobre et les meetings de la campagne : Pacha le siamois te résume tout. Pour ou contre ? 👇\n#jtdeschatons #actu #politique #chaton #jt #lfi #melenchon #assembleenationale"),
}
s.OUT = os.path.join(m.D, 'package_soir'); os.makedirs(s.OUT, exist_ok=True)
loop = asyncio.new_event_loop()
plan = {}
dates = {'rn': '2026-10-11', 'ren': '2026-10-12', 'eelv': '2026-10-13', 'lr': '2026-10-14', 'lfi': '2026-10-15'}
names = {'rn': 'RN', 'ren': 'Renaissance', 'eelv': 'Les Écologistes', 'lr': 'LR', 'lfi': 'LFI'}
for i, v in V.items():
    p = dly.PARTIES[v['party']]
    m.SCENES[i].update(text=v['text'], who=v['who'], rate=p['rate'], pitch=p['pitch'], episode=json.load(open(os.path.join(m.D, 'episodes.json')))['soir'][dates[v['party']]])
    s.HOOKS[i] = v['hook']; s.SLUG[i] = v['slug']
    s.render(i, loop)
    open(os.path.join(m.D, 'descriptions', v['slug'] + '.txt'), 'w', encoding='utf-8').write(v['desc'] + '\n')
    plan[dates[v['party']]] = {'parti': names[v['party']], 'video': f"package_soir/{v['slug']}.mp4", 'description': f"descriptions/{v['slug']}.txt"}
json.dump(dict(sorted(plan.items())), open(os.path.join(m.D, 'planning_soir.json'), 'w'), ensure_ascii=False, indent=1)
print('PLANNING À JOUR')
