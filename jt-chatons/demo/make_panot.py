"""Bonus : Mathilde Panot et le ruban d'Octobre rose (faits sourcés, pas de gag : sujet lié au cancer)."""
import asyncio, os
import make_tiktok as m, make_shorts as s, make_daily as dly
p = dly.PARTIES['lfi']
TEXT = ("Une députée qui refuse le ruban rose, scandale ou vrai débat ? "
        "Un : la députée LFI Mathilde Panot refuse de porter le ruban d'Octobre rose, selon Le Monde. "
        "Deux : elle veut que la lutte contre le cancer ne soit pas, je cite, du vernis rose, rapporte franceinfo. "
        "Trois : le gouvernement et le RN dénoncent ce choix, d'après Le Monde. "
        "Octobre rose, c'est le mois de la lutte contre le cancer du sein. "
        "Et toi, tu portes le ruban rose ? Oui ou non ?")
sc = dict(kind='party', shots=['lfi'], voice=p['voice'], color=p['color'], tag='LFI',
          who=f"{p['name']} · Sources : Le Monde, franceinfo", text=TEXT, rate='+8%', pitch=p['pitch'], gvoice=p['gvoice'], gstyle="reporter sérieux et posé, ton neutre et clair, sans humour")
m.SCENES.append(sc); i = len(m.SCENES) - 1
m.CLIP_NAMES.append('lfi')
s.HOOKS[i] = ('Elle refuse le ruban rose !', 'Pacha t’explique, sans blague')
s.SLUG[i] = 'Bonus-panot-octobre-rose'
s.OUT = os.path.join(m.D, 'bonus')
s.render(i, asyncio.new_event_loop())
