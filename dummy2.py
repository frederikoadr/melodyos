from hashlib import new
import random
from jinja2 import bccache
from midi2audio import FluidSynth
from music21.corpus.manager import parse
from musicgen import show_score, create_midi, play_sound
from random import sample
from datetime import datetime, time
from random import randint, randrange
from music21 import common, corpus, instrument, key, note, stream, converter, midi, scale, alpha, environment, chord, interval, roman
#from music21 import *
a = ['F4', 'D4', 'E4', 'A4', 'B4', 'A4', 'A4', 'C']


us = environment.UserSettings()
for key in sorted(us.keys()):
    print(key, us[key])

# environment.set('musicxmlPath', 'D:\\Software\\MuseScore 3\\bin\\MuseScore3.exe')

b = stream.Stream()
noteObj = note.Note('A4')
b.append(noteObj)
b.write('lily', 'cox')

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

# @click.command()
# @click.option('--email', prompt="E-mail address", type=int, callback=validate_email)
# @click.option('--password', hide_input=True, confirmation_prompt=True)
# def ask_email(email, password):
#     click.echo('Valid Email: ' + str(email))

# if __name__ == '__main__':
#     ask_email()

# # Crossover concept
# def play_sound(littleMelody):
#     sp = midi.realtime.StreamPlayer(littleMelody)
#     sp.play()

# littleMelody = stream.Stream()
# littleMelody.append(note.Note('C4'))
# littleMelody.append(note.Note('E4'))
# littleMelody.append(note.Note('G4'))
# littleMelody.append(note.Note('C5'))

# littleMelody2 = stream.Stream()
# littleMelody2.append(note.Note('E4'))
# littleMelody2.append(note.Note('F4'))
# littleMelody2.append(note.Note('D4'))
# littleMelody2.append(note.Note('C4'))

# newMed = stream.Stream()

# for count in range(int(len(littleMelody2)/2)):
#     newMed.append(littleMelody[count])
#     littleMelody[count] = littleMelody2[count]
# for count in range(int(len(littleMelody2)/2)):
#     newMed.append(littleMelody2[count+2])

# play_sound(littleMelody)
# play_sound(newMed)
