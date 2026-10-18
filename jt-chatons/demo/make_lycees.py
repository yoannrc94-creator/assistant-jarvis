"""Bonus : édition spéciale sérieuse sur la mobilisation lycéenne (pas de gag)."""
import asyncio, os
import make_tiktok as m, make_shorts as s
TEXT = ("Lycées bloqués : ce qu'on sait vraiment. "
        "Un : pourquoi ? Les lycéens dénoncent le manque de moyens et des bâtiments en mauvais état. "
        "Sur la plateforme de concertation du gouvernement, les plaintes portent surtout sur les emplois du temps et l'état des bâtiments. "
        "Deux : le bilan. Au 5 octobre, environ 715 policiers et gendarmes et 215 élèves avaient été blessés. "
        "Le ministre de l'Éducation parle aussi de plus de 100 personnels blessés. "
        "Trois : les réponses. L'IGPN a ouvert 24 enquêtes. "
        "Le gouvernement annonce 3 000 professeurs remplaçants. "
        "Ce lundi, l'intersyndicale est reçue par le gouvernement, et une grève est prévue mardi. "
        "Et dans ton lycée, comment ça se passe ?")
sc = dict(kind='anchor', shots=['v_anchor'], voice='fr-FR-HenriNeural', color='#b3262e', tag='ÉDITION SPÉCIALE',
          who='Maître Moustache · Sources : franceinfo, Sud Ouest, ici', text=TEXT, gvoice='Charon', gstyle="présentateur de journal télévisé, ton grave, posé et sérieux, clair", rate='+8%')
m.SCENES.append(sc); i = len(m.SCENES) - 1
m.CLIP_NAMES.append('anchor')
s.HOOKS[i] = ("Lycées bloqués, ce qu'on sait vraiment", 'Édition spéciale')
s.SLUG[i] = 'Bonus-lycees-edition-speciale'
s.OUT = os.path.join(m.D, 'bonus')
s.render(i, asyncio.new_event_loop())
