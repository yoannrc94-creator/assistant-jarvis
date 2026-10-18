"""Versions longues (30 à 40 s) des 6 vidéos courtes, textes tirés des titres de presse du 8 au 10 octobre 2026."""
import asyncio, sys
import make_tiktok as m, make_shorts as s
END = " À suivre dans le prochain JT des chatons."
LONG = {
 1: dict(who='Pacha le Siamois · Sources : LCP, ici, Le Bien Public', hook=('LFI : niche et meetings', 'le chaton te résume tout'),
         text="Ici Pacha, en direct de l'Assemblée. La France insoumise prépare sa niche parlementaire du 29 octobre. Selon LCP, ses textes porteront notamment sur les salaires, les pesticides et les AESH. Côté campagne, Jean-Luc Mélenchon, candidat à la présidentielle, est attendu en meeting près de Clermont-Ferrand dimanche, d'après ici. Et à Dijon, les députées Clémence Guetté et Aurélie Trouvé animent un meeting, rapporte Le Bien Public." + END),
 2: dict(who='Gaspard le Chartreux · Sources : site du RN, Sud Ouest, Les Echos', hook=('Le RN muscle sa campagne', 'le chaton te dit tout'),
         text="Ici Gaspard. Au Rassemblement national, l'équipe de campagne de Marine Le Pen accueille de nouveaux membres, a annoncé le parti sur son site. À l'Assemblée, le RN n'a pas réussi à faire adopter ses textes lors de sa niche parlementaire, selon Sud Ouest. Et pour la présidentielle 2027, sa proposition de taxe sur les salariés étrangers fait réagir les entreprises, d'après Les Echos." + END),
 3: dict(who='Mandarine la Maine Coon · Sources : France 3, Le Figaro, La Voix du Nord', hook=('Attal lance son pacte jeunesse', 'le chaton t’explique'),
         text="Ici Mandarine. En meeting à Lyon ce samedi, Gabriel Attal, candidat Renaissance, a présenté son pacte pour la jeunesse, selon France 3 Régions. Le Figaro évoque aussi un nouveau pacte générationnel et une double règle d'or. Par ailleurs, la sénatrice Brigitte Bourguignon, ancienne ministre, quitte Renaissance, rapporte La Voix du Nord." + END),
 4: dict(who='Pivoine la Persane · Sources : Libération, PS, Le Dauphiné, BFM', hook=('Primaire PS : 100 000 votants', 'le chaton a compté'),
         text="Ici Pivoine. La primaire du Parti socialiste et de Place publique se poursuit. Plus de 100 000 votants étaient comptés ce samedi à 18 heures, selon les organisateurs cités par Libération. Le vote est ouvert jusqu'à dimanche 18 heures, indique le Parti socialiste, et les résultats sont attendus dimanche, d'après Le Dauphiné Libéré. Après une cyberattaque contre le site de la primaire, le parquet de Paris a ouvert une enquête, rapporte BFM." + END),
 5: dict(who="Flocon l'Angora · Sources : franceinfo, La Voix du Nord, BFM", hook=('Les Écolos et 2027', 'le chaton enquête'),
         text="Ici Flocon. Chez Les Écologistes, Sandrine Rousseau appelle à accélérer le processus de désignation pour la présidentielle, rapporte franceinfo. Marine Tondelier est allée à la rencontre de lycéens mobilisés dans un café de Douai, selon La Voix du Nord. Elle accuse le gouvernement de parier sur le pourrissement du mouvement lycéen, d'après BFM." + END),
 6: dict(who='Bjorn le Norvégien · Sources : Ouest-France, Le Monde, BFM', hook=('Retailleau veut refaire l’école', 'le chaton t’explique'),
         text="Ici Bjorn. Pour Bruno Retailleau, candidat à la présidentielle, il faut une refonte complète du système éducatif, affirme-t-il dans un entretien à Ouest-France. Sa candidature reçoit le soutien de François Baroin, selon Le Monde. Et sur BFM, il désigne Jean-Luc Mélenchon comme son seul adversaire." + END),
}
s.OUT = s.os.path.join(m.D, 'package_tiktok_long'); s.os.makedirs(s.OUT, exist_ok=True)
loop = asyncio.new_event_loop()
for i in [int(x) for x in sys.argv[1:]] or range(1, 7):
    L = LONG[i]
    m.SCENES[i]['text'] = L['text']; m.SCENES[i]['who'] = L['who']
    s.HOOKS[i] = L['hook']
    s.render(i, loop)
