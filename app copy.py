import random
from flask import Flask, render_template, request, session
from matplotlib import pyplot as plt
import numpy as np
from musicgen import create_pdf, main, buat_chromosome, get_keyscale, create_midi, single_point_crossover, tournament_selection, mutation, noteLength
import secrets
import pyrebase

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
 
app.secret_key = secrets.token_urlsafe(16)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

ALLOWED_EXTENSIONS = set(['mid', 'midi', 'xml', 'pdf', 'mp3', 'wav', 'png', 'jpg', 'jpeg', 'gif'])

user_dict = {}
test = []
sum_fitnesses = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/', methods=['POST', 'GET'])
def start():
	path = ''
	ukey = ''
	generation_num = 1
	if request.method=='POST':
		stepValue = request.form["step"]
		if stepValue == "initiate":
			# token = secrets.token_urlsafe(16)
			ukey = str(request.form.get("Nickname"))
			age=int(request.form.get("Age"))
			experience = str(request.form.get("Experience"))

			population_size=int(request.form.get("numMelodies"))
			juml_not=int(request.form.get("numNotes"))
			scale=str(request.form.get("scale"))
			key=str(request.form.get("key"))
			instrument=str(request.form.get("inst"))
			
			population = [buat_chromosome(juml_not, scale, key, population_size) for _ in range(population_size)]
			path = create_midi(population, scale, key, generation_num, instrument)
			#create_pdf(population, scale, key, generation_num)
			print(population_size, juml_not, scale, key, instrument)
			
			session['user'] = ukey
			user_dict.update({ukey:[population, scale, key, generation_num, instrument, path]})
			print(user_dict)
		elif stepValue == "evaluate":
			if 'user' in session:
				ukey = session['user']
			rate = []
			population_size=int(request.form.get("numMelodies"))
			print("population size " + str(population_size))
			for x in range(population_size):
				rate.append(int(request.form.get("rating" + str(x+1))))
			
			sum_fitnesses.append(sum(rate))

			population_fitness = [(user_dict[ukey][0][idx], fitnes) for idx, fitnes in enumerate(rate)]
			selectedParents = []

			#tournament selection w/ removing selcted, for diversity among population; q:does it necessary?
			# while int(len(population_fitness)) > 1:
			# 	a = tournament_selection(population_fitness)
			# 	print("winner : " + str(a))
			# 	b = population_fitness.pop(a)[0] 
			# 	selectedParents.append(b)

			#opposite above loop
			pop_length = int(len(population_fitness))
			while pop_length > 1:
				a = tournament_selection(population_fitness)
				print("winner : " + str(a))
				b = population_fitness[a][0]
				selectedParents.append(b)
				pop_length -= 1
				
			selectedParents.append(population_fitness[0][0])
			offsprings = []
			for num in range(int(len(selectedParents))):
				# checking condition
				if num % 2 == 0:
					index = random.randint(1, int(len(selectedParents[num]))-1)
					print(str([str(p) for p in selectedParents[num].pitches]) + " cross w/ \n" + str([str(p) for p in selectedParents[num+1].pitches]) + " , indeks perpotongan : " + str(index))
					offspring_a, offspring_b = single_point_crossover(selectedParents[num], selectedParents[num+1], index)
					offsprings.append(offspring_a)
					offsprings.append(offspring_b)

			for num in range(int(len(offsprings))):
				offsprings[num] = mutation(offsprings[num], user_dict[ukey][1], user_dict[ukey][2], num=2, probability=0.5)
				print([str(p) for p in offsprings[num].pitches])
			
			user_dict[ukey][3] += 1
			user_dict[ukey][0] = offsprings
			path = create_midi(user_dict[ukey][0], user_dict[ukey][1], user_dict[ukey][2], user_dict[ukey][3], user_dict[ukey][4])
			user_dict[ukey][5] = path
		elif stepValue == "download":
			if 'user' in session:
				ukey = session['user']

			create_pdf(user_dict[ukey][0], user_dict[ukey][1], user_dict[ukey][2], user_dict[ukey][3])
			path = user_dict[ukey][5]

			temp_popu = user_dict[ukey][0]
			user_dict["sum_fitness"] = sum_fitnesses
			user_dict[ukey].pop(0)
			db.child(ukey).set(user_dict)
			user_dict[ukey].insert(0, temp_popu)

	return render_template("index.html", path=path, generation_num=user_dict[ukey][3])

@app.route('/data', methods=['POST', 'GET'])
def data():
	
	gen_list = []
	x_data = np.array(gen_list)
	y_data = np.array(sum_fitnesses)

	plt.plot(x_data, y_data)

	plt.title("Tingkat ketertarikan/fitness di setiap generasi")
	plt.xlabel("Generasi")
	plt.ylabel("Sum Fitness")

	plt.savefig('foo.png', bbox_inches='tight')
	return render_template("data.html")
# main driver function
# if __name__ == '__main__':
# 	app.run(debug=True)
