from hashlib import new
import random
from jinja2 import bccache
from midi2audio import FluidSynth
from music21.corpus.manager import parse
from musicgen import show_score, create_midi, play_sound
from random import sample
from datetime import datetime, time
from random import randint, randrange
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
import pyrebase
from music21 import common, corpus, instrument, key, note, stream, converter, midi, scale, alpha, environment, chord, interval, roman
from music21.converter.subConverters import ConverterMusicXML
import os
a = ['F4', 'D4', 'E4', 'A4', 'B4', 'A4', 'A4', 'C']
s = stream.Stream()

us = environment.UserSettings()
us['lilypondPath'] = 'LilyPond/usr/bin/lilypond.exe'
# for key in sorted(us.keys()):
#     print(key, us[key])
s.keySignature = key.Key('D', 'major')
for i in range(len(a)):
  s.append(note.Note(a[i]))

conv =  converter.subConverters.ConverterLilypond()
filepath = 'test'
conv.write(s, fmt = 'lilypond', fp=filepath, subformats = ['pdf'])

# conv_musicxml = ConverterMusicXML()
# scorename = 'myScoreName.xml'
# filepath = scorename
# out_filepath = conv_musicxml.write(s, 'musicxml', fp=filepath, subformats=['png'])

# environment.set('musicxmlPath', 'D:\\Software\\MuseScore 3\\bin\\MuseScore3.exe')


# fs = FluidSynth()
# fs.midi_to_audio('input.mid', 'output.wav')

# b.write("musicxml.pdf", fp='newtest')

# folder = str(int(datetime.now().timestamp()))
# os.makedirs(f"midi-generator/{folder}", exist_ok=True)
# meld.write('musicxml', fp=f"midi-generator/{folder}/test")

# meld.show('musicxml.pdf')

## def validate_email(ctx, param, value):
#     try:
#         if value > 5:
#             raise ValueError(value)
#         else:
#             return value
#     except ValueError as e:
#         click.echo('Incorrect email address given: {}'.format(e))
#         value = click.prompt(param.prompt)
#         return validate_email(ctx, param, value)
