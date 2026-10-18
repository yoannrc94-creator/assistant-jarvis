"""Voix de secours NVIDIA (Magpie multilingue, choisie par l'utilisateur le 14 octobre), après Gemini."""
import os, wave
D = os.path.dirname(os.path.abspath(__file__))
FEMMES = ('Denise', 'Vivienne', 'Eloise', 'Brigitte')

def say(text, out_wav, edge_voice=''):
    import riva.client, gem_align
    k = open(os.path.join(D, '.nvidia_key')).read().strip()
    auth = riva.client.Auth(use_ssl=True, uri='grpc.nvcf.nvidia.com:443',
                            metadata_args=[['function-id', '877104f7-e885-42b9-8de8-f6e4c6303969'], ['authorization', 'Bearer ' + k]])
    voice = 'Magpie-Multilingual.FR-FR.Louise' if any(f in edge_voice for f in FEMMES) else 'Magpie-Multilingual.FR-FR.Pascal.Happy'
    r = riva.client.SpeechSynthesisService(auth).synthesize(text, voice_name=voice, language_code='fr-FR', sample_rate_hz=44100)
    w = wave.open(out_wav, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100); w.writeframes(r.audio); w.close()
    dur = len(r.audio) / 2 / 44100
    if dur < 0.25 * len(text.split()): raise RuntimeError('voix NVIDIA trop courte')
    return out_wav, dur, gem_align.words_timing(out_wav, text, dur), voice
