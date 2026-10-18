"""Édition spéciale Covid : ce qu'on sait (présentateur, faits sourcés, ton calme, pas de conseil médical)."""
import asyncio, os
import make_tiktok as m, make_shorts as s
TEXT = ("Le Covid revient, vraiment ? Voici ce qu'on sait. "
        "Un : les consultations pour suspicion de Covid ont bondi de 19 pour cent en une semaine. "
        "Deux : aux urgences, les passages pour Covid ont augmenté de 22 pour cent en une semaine. "
        "Trois : la campagne de vaccination contre la grippe et le Covid commence demain, mardi 13 octobre, avec 25 millions de doses disponibles. "
                "Et toi, tu as remarqué plus de malades autour de toi ? Dis-le en commentaire !")
sc = dict(kind='anchor', shots=['v_anchor'], voice='fr-FR-HenriNeural', color='#1f8a70', tag='ÉDITION SPÉCIALE',
          who='Maître Moustache · Sources : BFM, Charente Libre, franceinfo', text=TEXT, rate='+10%',
          gvoice='Charon', gstyle="présentateur de journal télévisé, ton calme, clair et rassurant, rythme dynamique")
m.SCENES.append(sc); i = len(m.SCENES) - 1
m.CLIP_NAMES.append('anchor')
s.HOOKS[i] = ('Le Covid est de retour ?', "Ce qu'on sait vraiment")
s.SLUG[i] = 'Bonus-covid-edition-speciale'
s.OUT = os.path.join(m.D, 'bonus')
s.render(i, asyncio.new_event_loop())
