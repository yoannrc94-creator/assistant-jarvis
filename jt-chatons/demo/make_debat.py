"""Bonus débat : réseaux sociaux interdits avant 15 ans (présentateur, neutre, question pour ou contre)."""
import asyncio, os
import make_tiktok as m, make_shorts as s
TEXT = ("Interdit de TikTok avant 15 ans ? La Turquie l'a décidé. "
        "Un : l'interdiction y démarre le 1er novembre. "
        "Deux : en France, le gouvernement prépare une nouvelle version de son projet. "
        "Moi, j'ai neuf vies, mais aucun compte. "
        "Et toi, tu es pour ou contre ? Dis-le en commentaire !")
sc = dict(kind='anchor', shots=['v_anchor'], voice='fr-FR-HenriNeural', color='#7b3fe4', tag='LE DÉBAT',
          who='Maître Moustache · Sources : 20 Minutes, Le Matin, Le Monde', text=TEXT, gvoice='Charon', gstyle="présentateur de journal télévisé, voix posée, chaleureuse et claire, rythme dynamique", rate='+10%')
m.SCENES.append(sc); i = len(m.SCENES) - 1
m.CLIP_NAMES.append('anchor')
s.HOOKS[i] = ('Interdit de TikTok avant 15 ans ?', 'Le débat')
s.SLUG[i] = 'Bonus-debat-reseaux-sociaux'
s.OUT = os.path.join(m.D, 'bonus')
s.render(i, asyncio.new_event_loop())
