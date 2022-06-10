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
#from music21 import *
a = ['F4', 'D4', 'E4', 'A4', 'B4', 'A4', 'A4', 'C']


# us = environment.UserSettings()
# for key in sorted(us.keys()):
#     print(key, us[key])

# environment.set('musicxmlPath', 'D:\\Software\\MuseScore 3\\bin\\MuseScore3.exe')

firebaseConfig = {
  'apiKey': "AIzaSyC8BWJ8Y_9Y1I5em8tDywHFWT21tm8ThKo",
  'authDomain': "melodyos.firebaseapp.com",
  'databaseURL': "https://melodyos-default-rtdb.asia-southeast1.firebasedatabase.app",
  'projectId': "melodyos",
  'storageBucket': "melodyos.appspot.com",
  'messagingSenderId': "967726961597",
  'appId': "1:967726961597:web:cda3c38ffbed17488638d4",
  'measurementId': "G-84JQ3BP3ZL"
}
firebase = pyrebase.initialize_app(firebaseConfig)
db=firebase.database()

users=db.child("users").get()


plt.style.use('seaborn')
fig, ax = plt.subplots()
fig_single, ax_single = plt.subplots()
user_count = 0
highest = 0
x_all = []
y_all = []

ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.xaxis.set_major_locator(mtick.MultipleLocator(1))
ax.legend(loc='best')
ax.set_title("Tingkat ketertarikan/fitness di setiap iterasi")
ax.set_xlabel("Iterasi / Generasi-1")
ax.set_ylabel("Presentase ketertarikan/fitness")



for user in users.each():
    user_count += 1
    print(user.val())
    population_num = user.val()[2]

    sum_fit = []
    for single_sum_fit in user.val()[5]:
        single_sum_fit = single_sum_fit/(population_num*5)*100
        sum_fit.append(single_sum_fit)
    
    gen_list = np.arange(1, len(sum_fit)+1)

    x_all.append(gen_list)
    y_all.append(sum_fit)

    ax.plot(gen_list, sum_fit, 's-', label='User '+str(user_count))

    ax_single.cla()
    
    ax_single.plot(gen_list, sum_fit, 's-', label=user.key())
    ax_single.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax_single.xaxis.set_major_locator(mtick.MultipleLocator(1))
    ax_single.set_title("Tingkat ketertarikan/fitness di setiap iterasi")
    ax_single.set_xlabel("Iterasi / Generasi-1")
    ax_single.set_ylabel("Presentase ketertarikan/fitness")

    fig_single.savefig('static/uploads/fig'+str(user_count)+'.jpg', dpi=75)

for i in x_all:
  if highest < max(i):
      highest = max(i)
      mean_x_axis = i
ys_interp = [np.interp(mean_x_axis, x_all[i], y_all[i]) for i in range(len(x_all))]
mean_y_axis = np.mean(ys_interp, axis=0)
ax.plot(mean_x_axis, mean_y_axis, '--', label='Extrapolated Mean')


plt.tight_layout()
fig.savefig('static/uploads/avg_fig.jpg', dpi=75)

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
