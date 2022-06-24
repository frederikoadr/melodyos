from random import choices, randrange, sample
from datetime import datetime, time
from music21 import instrument, note, stream, converter, midi, scale, audioSearch, alpha, configure, key, environment
import os
import shutil
import matplotlib.pyplot as plt
import numpy as np
import random
import click

KEYS = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]
noteLength = [.5, 1, 2]



Chromosome = stream.Stream()
time_folder = str(int(datetime.now().timestamp()))

def buat_chromosome(jumlNot, scale, key, population_size) -> Chromosome:
    myscale = get_keyscale(scale, key)
    for x in range (population_size):
        littleMelody = stream.Stream()
        for i in range(jumlNot):
            if i == jumlNot-1:
                noteObj = note.Note(myscale.tonic)
                randomLength = random.choice(noteLength)
                noteObj.quarterLength = randomLength
                littleMelody.append(noteObj)
            else:
                #randomNotes = random.choice(cmajor.pitches)
                noteObj = note.Note(random.choice(myscale.getPitches()))
                randomLength = random.choice(noteLength)
                noteObj.quarterLength = randomLength
                littleMelody.append(noteObj)
        return littleMelody

def get_keyscale(scaleName: str, keysignature: str):
    if(scaleName == 'major'):
        myscale = scale.MajorScale(keysignature)
    elif(scaleName == 'minor'):
        myscale = scale.MinorScale(keysignature)
    elif(scaleName == 'dorian'):
        myscale = scale.DorianScale(keysignature)
    elif(scaleName == 'phrygian'):
        myscale = scale.PhrygianScale(keysignature)
    elif(scaleName == 'lydian'):
        myscale = scale.LydianScale(keysignature)
    elif(scaleName == 'mixolydian'):
        myscale = scale.MixolydianScale(keysignature)
    elif(scaleName == 'locrian'):
        myscale = scale.LocrianScale(keysignature)
    return(myscale)

def fitness(chromosome, inst):

    print("Nilai melodi dari 1 sampai 5 : ")
    play_sound(chromosome, inst)
    
    rating = input()

    #time.sleep(1)

    try:
        rating = int(rating)
        if(rating > 5 or rating < 1):
            rating = 1
    except ValueError:
        rating = 1

    return rating

def tournament_selection(population_fitness):
    candidates = sample(list(enumerate(population_fitness)), k=2)
    print("list " + str(candidates[0][0]) + " vs " + str(candidates[1][0]))
    return candidates[0][0] if candidates[0][1][1] > candidates[1][1][1] else candidates[1][0]

def rank_selection(total):
    rankList = [item for item in range(1, total+1)]
    max = sum(rankList)
    pick = random.uniform(0, max)
    current = 0
    for key, value in enumerate(rankList):
        current += value
        if current > pick:
            return key

def single_point_crossover(a, b, index):
    lengthMelodyA = int(len(a))
    if(lengthMelodyA == int(len(b))):
        newMelodyA = stream.Stream()
        newMelodyB = stream.Stream()

        for t in b[:index]:
            newMelodyA.append(t)
        for t in a[index:]:
            newMelodyA.append(t)

        for t in a[:index]:
            newMelodyB.append(t)
        for t in b[index:]:
            newMelodyB.append(t)

        return newMelodyB, newMelodyA
    else:
        print("panjang tidak sama!")
        return a, b

def multi_point_crossover(A, B, multi_index):
    for i in multi_index:
        A, B = single_point_crossover(A, B, i)
    return A, B

def mutation(melody: Chromosome, scale, key, num: int, probability: float) -> Chromosome:
    myscale = get_keyscale(scale, key)
    for _ in range(num):
        if (random.random() < probability):
            index = random.randint(0, int(len(melody) - 2))
            print("indeks mutasi : " + str(index))
            a = note.Note(random.choice(myscale.getPitches()))
            a.quarterLength = melody[index].quarterLength
            melody.replace(melody[index], a)
    return melody


def play_sound(littleMelody: Chromosome, inst="piano"):
    if(inst == "violin"):
        littleMelody.insert(instrument.Violin())
        sp = midi.realtime.StreamPlayer(littleMelody)
        sp.play()
        littleMelody.pop(0)
    if(inst == "guitar"):
        littleMelody.insert(instrument.Guitar())
        sp = midi.realtime.StreamPlayer(littleMelody)
        sp.play()
        littleMelody.pop(0)
    else:
        sp = midi.realtime.StreamPlayer(littleMelody)
        sp.play()

def show_score(show_format: str, mel, tngganada, nd_dasar):
    mel.keySignature = key.Key(nd_dasar, tngganada)
    mel.show(show_format)
    mel.pop(0)

def create_midi(population, tngganada, nd_dasar, generation_id, inst):
    os.makedirs(f"static/uploads/{time_folder}/{generation_id}", exist_ok=True)
    allFiles = []
    for count, x in enumerate(population):
        if(inst == "piano"):
            x.insert(instrument.Piano())
        if(inst == "violin"):
            x.insert(instrument.Violin())
        if(inst == "guitar"):
            x.insert(instrument.Guitar())
        if(inst == "flute"):
            x.insert(instrument.Flute())
        if(inst == "trumpet"):
            x.insert(instrument.Trumpet())
        if(inst == "saxophone"):
            x.insert(instrument.Saxophone())
        if(inst == "marimba"):
            x.insert(instrument.Marimba())
        
        x.keySignature = key.Key(nd_dasar, tngganada)
        fp=f"static/uploads/{time_folder}/{generation_id}/rank"+ str(count+1) + "_" + nd_dasar + tngganada
        allFiles.append(fp)
        x.write('midi', fp + '.mid')
        x.pop(0)
        x.pop(0)

    fp_prev = f"static/uploads/{time_folder}/{generation_id-1}"
    if os.path.exists(fp_prev) and os.path.isdir(fp_prev):
        shutil.rmtree(fp_prev)
        # allFiles.append(f"static/uploads/{time_folder}/{generation_id}/test"+ str(count) +'.mid')
    return allFiles

def create_pdf(music21stream, tngganada, nd_dasar, generation_id, count):
    os.makedirs(f"static/uploads/{time_folder}/{generation_id}", exist_ok=True)
    conv =  converter.subConverters.ConverterLilypond()

    music21stream.keySignature = key.Key(nd_dasar, tngganada)
    filepath = f"static/uploads/{time_folder}/{generation_id}/rank"+ count + "_" + nd_dasar + tngganada
    respath = conv.write(music21stream, fmt = 'lilypond', fp=filepath, subformats = ['pdf'])
    music21stream.pop(0)
    return respath

def create_multi_pdf(population, tngganada, nd_dasar, generation_id):
    os.makedirs(f"static/uploads/{time_folder}/{generation_id}", exist_ok=True)
    us = environment.UserSettings()
    us['lilypondPath'] = 'LilyPond/usr/bin/lilypond.exe'
    conv =  converter.subConverters.ConverterLilypond()
    for count, x in enumerate(population):
        x.keySignature = key.Key(nd_dasar, tngganada)
        filepath = f"static/uploads/{time_folder}/{generation_id}/rank"+ str(count) + "_" + nd_dasar + tngganada
        conv.write(x, fmt = 'lilypond', fp=filepath, subformats = ['pdf'])
        x.pop(0)
    #s = corpus.parse(littleMelody)
    #littleMelody.show('midi')
    #littleMelody.clear()