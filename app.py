from collections import UserDict
import random
from flask import Flask, render_template, request, session, current_app, flash, redirect, url_for, send_from_directory, current_app
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from musicgen import create_multi_xml, create_pdf, create_chromosome, get_keyscale, create_midi, single_point_crossover, tournament_selection, mutation
import pyrebase
import os
import jsonpickle
from copy import deepcopy
from flask_session import Session
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') #secrets.token_urlsafe(16)
UPLOAD_FOLDER = 'uploads/'
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Set up Firebase config using environment variables
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

firebase = pyrebase.initialize_app(firebase_config)
db=firebase.database()

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/', methods=['POST', 'GET'])
def start():
	user_dict = {}
	generation_num = 1
	if request.method=='POST':
		sum_fitnesses = []

		ukey = str(request.form.get("Nickname"))
		age=int(request.form.get("Age"))
		email = str(request.form.get("email"))
		experience = str(request.form.get("Experience"))

		population_size=int(request.form.get("numMelodies"))
		juml_not=int(request.form.get("numNotes"))
		scale=str(request.form.get("scale"))
		key=str(request.form.get("key"))
		instrument=str(request.form.get("inst"))
		
		population = [create_chromosome(juml_not, scale, key, population_size) for _ in range(population_size)]
		path = create_midi(population, scale, key, generation_num, instrument)
		
		silentremove('static/uploads/user_fig.jpg')

		popu_encoded = jsonpickle.encode(population)

		user_dict.update({ukey:{"db_data":[scale, key, generation_num, instrument, path, sum_fitnesses, age, experience, email], "population":popu_encoded}})
		session['user'] = ukey
		session['user_dict'] = user_dict

		db.child("users").child(ukey).set(user_dict[ukey]["db_data"])

	return render_template("evaluate.html", path=path, generation_num=user_dict[ukey]["db_data"][2])

@app.route('/evaluate', methods=['POST', 'GET'])
def evaluate():
	if request.method=='POST':
		if 'user' in session:
			ukey = deepcopy(session['user'])
		user_dict = deepcopy(session['user_dict'])
		# if user_dict:
		# 	population_size = len(user_dict[ukey]["population"])
		# else:
		population_size = 4
		popu_decoded = jsonpickle.decode(user_dict[ukey]["population"])

		rate = []
		print("population size " + str(population_size))
		for x in range(population_size):
			rate.append(int(request.form.get("rating" + str(x+1))))
		
		user_dict[ukey]["db_data"][5].append(sum(rate))

		population_fitness = [(popu_decoded[idx], fitnes) for idx, fitnes in enumerate(rate)]
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
			# print("winner : " + str(a))
			b = population_fitness[a][0]
			selectedParents.append(b)
			pop_length -= 1
			
		selectedParents.append(population_fitness[0][0])
		offsprings = []
		for num in range(int(len(selectedParents))):
			# checking condition
			if num % 2 == 0:
				index = random.randint(1, int(len(selectedParents[num]))-1)
				# print(str([str(p) for p in selectedParents[num].pitches]) + " cross w/ \n" + str([str(p) for p in selectedParents[num+1].pitches]) + " , indeks perpotongan : " + str(index))
				offspring_a, offspring_b = single_point_crossover(selectedParents[num], selectedParents[num+1], index)
				# print('hasil :')
				# print(str([str(p) for p in offspring_a.pitches]) + "\n" + str([str(p) for p in offspring_b.pitches]) + "\n")
				offsprings.append(offspring_a)
				offsprings.append(offspring_b)

		for num in range(int(len(offsprings))):
			offsprings[num] = mutation(offsprings[num], user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], num=int(len(offsprings[num])/4), probability=0.5)

		user_dict[ukey]["db_data"][2] += 1
		user_dict[ukey]["population"] = jsonpickle.encode(offsprings)
		path = create_midi(offsprings, user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2], user_dict[ukey]["db_data"][3])
		user_dict[ukey]["db_data"][4] = path

		session['ukey'] = ukey
		session['user_dict'] = user_dict
		session.modified = True

	return render_template("evaluate.html", path=path, generation_num=user_dict[ukey]["db_data"][2])

@app.route('/download', methods=['POST', 'GET'])
def download():
	if request.method=='POST':
		if 'user' in session:
			ukey = session['user']
		user_dict = session['user_dict']
		popu_decoded = jsonpickle.decode(user_dict[ukey]["population"])

		create_multi_xml(popu_decoded, user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2], ukey)

		db.child("users").child(ukey).set(user_dict[ukey]["db_data"])

		create_figure(ukey, user_dict)

	return render_template("download.html", user_dict=user_dict[ukey]["db_data"], done=True)

# # @app.route('/downloadpdf/<path:index_pop>', methods=['POST', 'GET'])
# # def downloadpdf(index_pop):
# # 	if 'user' in session:
# # 		ukey = session['user']
# # 	global user_dict
# # 	pdfpath = create_pdf(user_dict[ukey]["population"][int(index_pop)-1], user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2], index_pop)

# 	return send_file(pdfpath, as_attachment=True)

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
	mean_x_axis = np.array([])  # Initialize mean_x_axis to an empty array
	for user in users.each():
		user_count += 1
		population_num = 4

		sum_fit = []
		for single_sum_fit in user.val()[5]:
			single_sum_fit = single_sum_fit/(population_num*5)*100
			sum_fit.append(single_sum_fit)
		
		gen_list = np.arange(1, len(sum_fit)+1)

		x_all.append(gen_list)
		y_all.append(sum_fit)

		ax.plot(gen_list, sum_fit, 'o-', label='User '+str(user_count))

		ax_single.cla()
    
		ax_single.plot(gen_list, sum_fit, 's-', label='User '+str(user_count))
		save_figure(ax_single, fig_single, str(user_count))
		
		users_data.append([user.key(), user.val()[0], user.val()[1], user.val()[2], user.val()[3], user.val()[6], user.val()[7], user.val()[8]])

	for i in x_all:
		if highest < max(i):
			highest = max(i)
			mean_x_axis = i
	ys_interp = [np.interp(mean_x_axis, x_all[i], y_all[i]) for i in range(len(x_all))]
	mean_y_axis = np.mean(ys_interp, axis=0)
	ax.plot(mean_x_axis, mean_y_axis, '--', label='Mean')
	save_figure(ax, fig, 'sum')

	ax_single.cla()
	mean_list = mean_y_axis
	df_rolling = rolling_mean(mean_list, window=2)
	for i, v in enumerate(mean_y_axis):
		ax_single.text(i, v+25, "%d" %v, ha="center")
	ax_single.plot(mean_x_axis, mean_y_axis, 'o--', label='Mean')
	ax_single.plot(mean_x_axis, df_rolling, label='Moving Average')
	save_figure(ax_single, fig_single, 'avg')

	ax_single.cla()
	t = np.mean(pct_change_percent(mean_list))
	print(t)

	ax_single.cla()
	list_iteration = []
	for j in users_data:
		list_iteration.append(j[3]-1)
	ax_single.hist(list_iteration)
	ax_single.xaxis.set_major_locator(mtick.MultipleLocator(1))
	ax_single.set_title("Jumlah iterasi di setiap pengguna")
	ax_single.set_xlabel("Jumlah iterasi")
	ax_single.set_ylabel("Jumlah pengguna")
	plt.tight_layout()
	fig_single.savefig('static/uploads/fig_histogram.jpg', dpi=65)
	epoch_mean = np.mean(list_iteration)
	return render_template("data.html", users_data=users_data, epoch_mean=epoch_mean, s=s.values.tolist() , t=s.pct_change().mul(100).values.tolist())

def create_figure(ukey, user_dict):
	population_num = 4

	plt.style.use('seaborn-v0_8-whitegrid')
	fig, ax = plt.subplots()

	sum_fit = []
	for single_sum_fit in user_dict[ukey]["db_data"][5]:
		single_sum_fit = single_sum_fit/(population_num*5)*100
		sum_fit.append(single_sum_fit)
	
	gen_list = np.arange(1, len(sum_fit)+1)
	ax.plot(gen_list, sum_fit, 'o-', label=ukey)
	save_figure(ax, fig, 'single')

def save_figure(ax, fig, pathid):
	ax.yaxis.set_major_formatter(mtick.PercentFormatter())
	ax.xaxis.set_major_locator(mtick.MultipleLocator(1))
	ax.legend(loc='best')
	ax.set_title("Tingkat ketertarikan/fitness di setiap iterasi")
	ax.set_xlabel("Iterasi / Generasi-1")
	ax.set_ylabel("Presentase ketertarikan/fitness")
	plt.tight_layout()
	fig.savefig('static/uploads/fig_' + pathid + '.jpg', dpi=65)

def rolling_mean(arr, window=2):
    res = []
    for i in range(len(arr)):
        start = max(0, i - window + 1)
        window_slice = arr[start:i+1]
        res.append(sum(window_slice) / len(window_slice))
    return res
  
def pct_change_percent(arr):
	res = [0.0]  # Start with 0.0 for consistent float type
	for i in range(1, len(arr)):
			prev = arr[i-1]
			if prev == 0:
					res.append(0.0)
			else:
					res.append((arr[i] - prev)/abs(prev)*100)
	return res

# main driver function
if __name__ == '__main__':
	app.run(debug=True)
