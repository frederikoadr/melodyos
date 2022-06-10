import random
from flask import Flask, render_template, request, session, flash, redirect, url_for
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from musicgen import create_pdf, main, buat_chromosome, get_keyscale, create_midi, single_point_crossover, tournament_selection, mutation, noteLength
import secrets
import pyrebase
import os
from dotenv import load_dotenv

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
 
app.secret_key = secrets.token_urlsafe(16)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

firebase_config = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID'),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
}

firebase = pyrebase.initialize_app(firebaseConfig)
db=firebase.database()

ALLOWED_EXTENSIONS = set(['mid', 'midi', 'xml', 'pdf', 'mp3', 'wav', 'png', 'jpg', 'jpeg', 'gif'])

user_dict = {}
test = []
sum_fitnesses = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/login', methods = ['GET', 'POST'])
def login():
   error = None
   
   if request.method == 'POST':
      if request.form['username'] != 'admin' or \
         request.form['password'] != 'admin':
         error = 'Invalid username or password. Please try again!'
      else:
         flash('You were successfully logged in')
         return redirect(url_for('index'))
   return render_template('login.html', error = error)



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
			
			silentremove('static/uploads/user_fig.jpg')

			session['user'] = ukey
			user_dict.update({ukey:{"db_data":[scale, key, generation_num, instrument, path, sum_fitnesses, age, experience], "population":population}})
			
	return render_template("index.html", path=path, generation_num=user_dict[ukey]["db_data"][2])

@app.route('/evaluate', methods=['POST', 'GET'])
def evaluate():
	if request.method=='POST':
		if 'user' in session:
			ukey = session['user']
		rate = []
		population_size= len(user_dict[ukey]["db_data"][4])
		print("population size " + str(population_size))
		for x in range(population_size):
			rate.append(int(request.form.get("rating" + str(x+1))))
		
		user_dict[ukey]["db_data"][5].append(sum(rate))

		population_fitness = [(user_dict[ukey]["population"][idx], fitnes) for idx, fitnes in enumerate(rate)]
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
			offsprings[num] = mutation(offsprings[num], user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], num=2, probability=0.5)
			print([str(p) for p in offsprings[num].pitches])
		
		user_dict[ukey]["db_data"][2] += 1
		user_dict[ukey]["population"] = offsprings
		path = create_midi(user_dict[ukey]["population"], user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2], user_dict[ukey]["db_data"][3])
		user_dict[ukey]["db_data"][4] = path
	return render_template("index.html", path=path, generation_num=user_dict[ukey]["db_data"][2])

@app.route('/download', methods=['POST', 'GET'])
def download():
	if request.method=='POST':
		if 'user' in session:
			ukey = session['user']

		create_pdf(user_dict[ukey]["population"], user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2])
		path = user_dict[ukey]["db_data"][4]

		db.child("users").child(ukey).set(user_dict[ukey]["db_data"])

		plt.style.use('seaborn')
		fig, ax = plt.subplots()
		population_num = user_dict[ukey]["db_data"][2]

		sum_fit = []
		for single_sum_fit in user_dict[ukey]["db_data"][5]:
			single_sum_fit = single_sum_fit/(population_num*5)*100
			sum_fit.append(single_sum_fit)
		
		gen_list = np.arange(1, len(sum_fit)+1)
		ax.plot(gen_list, sum_fit, 's-', label=ukey)
		ax.yaxis.set_major_formatter(mtick.PercentFormatter())
		ax.xaxis.set_major_locator(mtick.MultipleLocator(1))
		ax.legend(loc='best')
		ax.set_title("Tingkat ketertarikan/fitness di setiap iterasi")
		ax.set_xlabel("Iterasi / Generasi-1")
		ax.set_ylabel("Presentase ketertarikan/fitness")
		plt.tight_layout()
		fig.savefig('static/uploads/user_fig.jpg', dpi=65)

	return render_template("index.html", path=path, generation_num=user_dict[ukey]["db_data"][2], done=True)

@app.route('/datadmin', methods=['POST', 'GET'])
def data():
	users=db.child("users").get()
	plt.style.use('seaborn')
	fig, ax = plt.subplots()
	fig_single, ax_single = plt.subplots()
	user_count = 0
	highest = 0
	x_all = []
	y_all = []
	users_data = []
	for user in users.each():
		user_count += 1
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
		
		users_data.append([user.key(), user.val()[0], user.val()[1], user.val()[2], user.val()[3], user.val()[6], user.val()[7]])

	for i in x_all:
		if highest < max(i):
			highest = max(i)
			mean_x_axis = i
	ys_interp = [np.interp(mean_x_axis, x_all[i], y_all[i]) for i in range(len(x_all))]
	mean_y_axis = np.mean(ys_interp, axis=0)
	ax.plot(mean_x_axis, mean_y_axis, '--', label='Extrapolated Mean')

	ax.yaxis.set_major_formatter(mtick.PercentFormatter())
	ax.xaxis.set_major_locator(mtick.MultipleLocator(1))
	ax.legend(loc='best')
	ax.set_title("Tingkat ketertarikan/fitness di setiap iterasi")
	ax.set_xlabel("Iterasi / Generasi-1")
	ax.set_ylabel("Presentase ketertarikan/fitness")
	plt.tight_layout()
	fig.savefig('static/uploads/last_fig.jpg', dpi=75)

	return render_template("data.html", users_data=users_data)

# main driver function
# if __name__ == '__main__':
# 	app.run(debug=True)
