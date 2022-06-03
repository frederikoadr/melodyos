from random import choices, randrange, sample
from datetime import datetime, time
from music21 import corpus, instrument, note, stream, converter, midi, scale, audioSearch, alpha, configure, key
from music21.environment import keys
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
        fp=f"static/uploads/{time_folder}/{generation_id}/rank"+ str(count) + "_" + inst + "_" + nd_dasar + tngganada
        allFiles.append(fp)
        x.write('midi', fp + '.mid')
        x.pop(0)
        x.pop(0)

    fp_prev = f"static/uploads/{time_folder}/{generation_id-1}"
    if os.path.exists(fp_prev) and os.path.isdir(fp_prev):
        shutil.rmtree(fp_prev)
        # allFiles.append(f"static/uploads/{time_folder}/{generation_id}/test"+ str(count) +'.mid')
    return allFiles

def create_pdf(population, tngganada, nd_dasar, generation_id):
    os.makedirs(f"static/uploads/{time_folder}/{generation_id}", exist_ok=True)
    for count, x in enumerate(population):
        x.keySignature = key.Key(nd_dasar, tngganada)
        x.write('musicxml', fp=f"static/uploads/{time_folder}/{generation_id}/test"+ str(count))
        x.pop(0)
    #s = corpus.parse(littleMelody)
    #littleMelody.show('midi')
    #littleMelody.clear()

print("===MUSIC COMPOSITION GENERATION===")
@click.command()
@click.option("--juml-pop", default=4, prompt='Jumlah populasi / melodi', type=int)
# @click.option("--juml-not", default=8, prompt='Jumlah not', type=int)
# @click.option("--instrumen", default="Piano", prompt='Pilih alat musik', type=click.Choice(ALAT_MUSIK, case_sensitive=False))
@click.option("--nd-dasar", default="C", prompt='Nada dasar', type=click.Choice(KEYS, case_sensitive=False))
# @click.option("--tngganada", default='major', prompt='Tangga nada', type=click.Choice(SCALES, case_sensitive=False))
@click.option("--num-mutations", default=2, prompt='Jumlah mutasi', type=int)
@click.option("--mutation-probability", default=0.5, prompt='Probabilitas mutasi', type=float)
def main(juml_pop: int, juml_not: int, instrumen: str, nd_dasar: str, tngganada: str, num_mutations: int, mutation_probability: float):

    generation_id = 1

    gen_list = []
    sum_fitnesses = []

    population_size = juml_pop

    mtd_seleksi = "tournament"

    if(tngganada == 'major'):
        myscale = scale.MajorScale(nd_dasar)
    elif(tngganada == 'minor'):
        myscale = scale.MinorScale(nd_dasar)

    population = [buat_chromosome(juml_not, myscale, population_size) for _ in range(population_size)]

    lanjut = True
    while lanjut:
        gen_list.append(generation_id)
        
        population_fitness = [(chromosome, fitness(chromosome, instrumen)) for chromosome in population]
        #population_fitness = [(chromosome, randrange(1,5)) for chromosome in population]

        #sorted_population_fitness = sorted(population_fitness, key=lambda e: e[1], reverse=False)

        population = [e[0] for e in population_fitness]

        sum_fitnesses.append(sum([e[1] for e in population_fitness]))

        for melodies in population_fitness:
            print(str([str(p) for p in melodies[0].pitches]) + ' = ' + str(melodies[1]))

        selectedParents = []
        if(mtd_seleksi == "tournament"):
            while int(len(population_fitness)) > 1:
                a = tournament_selection(population_fitness)
                print("winner : " + str(a))
                b = population_fitness.pop(a)[0]
                selectedParents.append(b)
            selectedParents.append(population_fitness[0][0])

        if(mtd_seleksi == "rank"):
            for j in range(int(len(population))):
                selectedParents.append(population[rank_selection(int(len(population)))])

        print("urutan parent :")
        for num in range(int(len(selectedParents))):
            print([str(p) for p in selectedParents[num].pitches])
        print("\n")

        offsprings = []
        for num in range(int(len(selectedParents))):
            # checking condition
            if num % 2 == 0:
                # listIndex = []
                # for i in range(1, int(len(selectedParents[num])-1)):
                #     listIndex.append(i)
                # index = sample(listIndex, k=2)
                # while abs(index[0]-index[1]) <= 1:
                #     index = sample(listIndex, k=2)
                index = random.randint(1, int(len(selectedParents[num]))-1)
                print(str([str(p) for p in selectedParents[num].pitches]) + " cross w/ \n" + str([str(p) for p in selectedParents[num+1].pitches]) + " , indeks perpotongan : " + str(index))
                offspring_a, offspring_b = single_point_crossover(selectedParents[num], selectedParents[num+1], index)
                offsprings.append(offspring_a)
                offsprings.append(offspring_b)
        
        #offspring_a, offspring_b = single_point_crossover(selectedParents[0], selectedParents[1])
        print('sp crossover results :')
        for num in range(int(len(offsprings))):
            print([str(p) for p in offsprings[num].pitches])

        print('mutation results :')
        for num in range(int(len(offsprings))):
            offsprings[num] = mutation(offsprings[num], myscale, num=num_mutations, probability=mutation_probability)
            print([str(p) for p in offsprings[num].pitches])

        print("generasi " + str(generation_id) + " selesai!")
        print("hasil 2 terbaik :")
        
        i = 1
        for num in offsprings[:2]:
            print("memainkan peringkat " + str(i) + " ...")
            i +=1
            play_sound(num, instrumen)

        create_midi(offsprings, tngganada, nd_dasar, generation_id) if input("apakah mau simpan ke midi? [y/n]") == "y" else print("melodi tidak disimpan")
        lanjut = input("lanjut? [y/n]") != "n"
        population = offsprings
        generation_id += 1
    
    if(input("ingin lihat dan simpan sheet melodi terbaik? [y/n]") == "y"):
        show_score('musicxml.pdf', offsprings[0], tngganada, nd_dasar)
        create_pdf(offsprings, tngganada, nd_dasar, generation_id-1)

    if(generation_id > 2 and input("ingin lihat data? [y/n]") == "y"):
        x = np.array(gen_list)
        y = np.array(sum_fitnesses)

        plt.plot(x, y)

        plt.title("Data fitness di setiap generasi")
        plt.xlabel("Generasi")
        plt.ylabel("Sum Fitness")

        plt.savefig('foo.png', bbox_inches='tight')

if __name__ == '__main__':
    main()
