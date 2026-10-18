"""Refait une vidéo du soir avec l'actu fraîche du jour (réutilise l'animation existante du chaton du parti).

Usage : python3 make_soir_refresh.py soir/config-AAAA-MM-JJ.json
config : {"date", "party", "hook1", "hook2", "text", "reaction", "question", "source", "description"}
Écrit package_soir/<slug>.mp4 et descriptions/<slug>.txt (slug lu dans planning_soir.json).
"""
import asyncio, json, os, sys
import make_tiktok as m, make_shorts as s, make_daily as dly

cfg = json.load(open(sys.argv[1]))
p = dly.PARTIES[cfg['party']]
plan = json.load(open(os.path.join(m.D, 'planning_soir.json')))[cfg['date']]
slug = os.path.splitext(os.path.basename(plan['video']))[0]
ep = json.load(open(os.path.join(m.D, 'episodes.json')))['soir'][cfg['date']]
text = ' '.join(x for x in (cfg['text'].rstrip(), cfg.get('reaction', p['catch']), cfg.get('question', 'Et toi, tu en penses quoi ?')) if x)
sc = dict(kind='party', shots=[cfg['party']], episode=ep, voice=p['voice'], color=p['color'], tag=p['tag'],
          who=f"{p['name']} · Sources : {cfg['source']}", text=text, rate=p['rate'], pitch=p['pitch'], gvoice=p['gvoice'], gstyle=p['gstyle'])
m.SCENES.append(sc); i = len(m.SCENES) - 1
m.CLIP_NAMES.append(cfg['party'])            # clips/<parti>.mp4 : animation déjà prête
s.HOOKS[i] = (cfg['hook1'], cfg['hook2']); s.SLUG[i] = slug
s.OUT = os.path.join(m.D, 'package_soir')
s.render(i, asyncio.new_event_loop())
open(os.path.join(m.D, 'descriptions', slug + '.txt'), 'w', encoding='utf-8').write(cfg['description'].strip() + '\n')
print('SOIR À JOUR', slug, 'épisode', ep)
