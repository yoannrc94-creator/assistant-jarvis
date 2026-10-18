import asyncio, ssl, aiohttp, edge_tts, inspect, sys
print('params:', list(inspect.signature(edge_tts.Communicate.__init__).parameters))
import edge_tts.communicate as _c
_c._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
async def go(voice, text, out):
    ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
    c = edge_tts.Communicate(text, voice)
    await c.save(out)
asyncio.run(go('fr-FR-HenriNeural', "Bonsoir, et bienvenue dans le JT des chatons. Ce soir, nos six reporters font le tour des partis politiques.", 'voix-henri.mp3'))
asyncio.run(go('fr-FR-DeniseNeural', "Ici Pacha le Siamois, en direct. La France insoumise prépare sa niche parlementaire du 29 octobre.", 'voix-denise.mp3'))
