"""Test : vidéo PS du jour avec la voix Gemini."""
import asyncio, json, os, subprocess
import make_tiktok as m, make_shorts as s, make_daily as dly, gem_tts, gem_align

STYLE = {'ps': ("jeune journaliste de télé précieuse et perfectionniste, très expressive et enjouée, rythme rapide et dynamique, petit air fier sur les chiffres", 'Kore')}
_old = m.tts
async def tts(i, sc):
    if 'gem' not in sc: return await _old(i, sc)
    style, voice = sc['gem']
    wav = os.path.join(m.D, f'gem_voice{i}.wav')
    if os.environ.get('REUSE'):                       # test : réutilise l'audio déjà généré (quota limité)
        import shutil, wave, gem_check; shutil.copy(os.environ['REUSE'], wav)
        with wave.open(wav) as w: dur = w.getnframes() / w.getframerate()
        return wav, dur, gem_align.words_timing_anchored(wav, sc['text'], dur, gem_check.transcribe(wav))
    wav, dur, words, _ = gem_tts.say_aligned(sc['text'], wav, voice, style)
    return wav, dur, words
m.tts = tts

c = json.load(open(os.path.join(m.D, 'daily/config-2026-10-11.json'))); p = dly.PARTIES['ps']
text = ' '.join([c['text'], c['reaction'], c['question']])
sc = dict(kind='party', shots=['daily_2026-10-11_ps'], episode=2, voice=p['voice'], color=p['color'], tag=p['tag'],
          who=f"{p['name']} · Source : {c['source']}", text=text, gem=STYLE['ps'])
m.SCENES.append(sc); i = len(m.SCENES) - 1; m.CLIP_NAMES.append('daily_2026-10-11_ps')
s.HOOKS[i] = (c['hook1'], c['hook2']); s.SLUG[i] = 'TEST-voix-Gemini-PS'; s.OUT = os.path.join(m.D, 'bonus')
s.render(i, asyncio.new_event_loop())
