from collections import Counter, UserDict
import random
import traceback
from flask import Flask, jsonify, render_template, request, session, send_file
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
from musicgen import create_multi_xml, create_pdf, create_chromosome, get_keyscale, create_midi, single_point_crossover, tournament_selection, mutation
import pyrebase
import os
import jsonpickle
from copy import deepcopy
from flask_session import Session
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.storage import Storage
from storage_service import StorageService


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') #secrets.token_urlsafe(16)
UPLOAD_FOLDER = 'uploads/'
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['SESSION_FILE_THRESHOLD'] = 500
Session(app)

# --- Appwrite setup ---
client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

storage = Storage(client)
storage_service = StorageService()

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

    if request.method == 'POST':
        sum_fitnesses = []

        ukey = str(request.form.get("Nickname"))
        age = int(request.form.get("Age") or 0)
        email = str(request.form.get("email"))
        experience = str(request.form.get("Experience"))

        population_size = int(request.form.get("numMelodies") or 4)
        juml_not = int(request.form.get("numNotes") or 8)
        scale = str(request.form.get("scale"))
        key_name = str(request.form.get("key"))
        instrument_name = str(request.form.get("inst"))

        population = [
            create_chromosome(juml_not, scale, key_name, population_size)
            for _ in range(population_size)
        ]

        local_paths = create_midi(
            population,
            scale,
            key_name,
            generation_num,
            instrument_name,
        )
        midi_urls = []
        for path in local_paths:
            url = storage_service.upload_file(path)
            midi_urls.append(url)

        popu_encoded = jsonpickle.encode(population)

        user_dict.update({
            ukey: {
                "db_data": [
                    scale, key_name, generation_num, instrument_name,
                    midi_urls, sum_fitnesses, age, experience, email
                ],
                "population": popu_encoded,
            }
        })

        session['user'] = ukey
        session['user_dict'] = user_dict

        db.child("users").child(ukey).set(user_dict[ukey]["db_data"])

        return render_template(
            "evaluate.html",
            urls=midi_urls,
            generation_num=user_dict[ukey]["db_data"][2]
        )

    return render_template("index.html")

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
            rate.append(int(request.form.get("rating" + str(x+1)) or 1))
        
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
        local_paths = create_midi(
            offsprings,
            user_dict[ukey]["db_data"][0],
            user_dict[ukey]["db_data"][1],
            user_dict[ukey]["db_data"][2],
            user_dict[ukey]["db_data"][3],
            )
        
        midi_urls = []
        for path in local_paths:
            url = storage_service.upload_file(path)
            midi_urls.append(url)
            
        user_dict[ukey]["db_data"][4] = midi_urls
        
        session['ukey'] = ukey
        session['user_dict'] = user_dict
        session.modified = True
    return render_template("evaluate.html", urls=midi_urls, generation_num=user_dict[ukey]["db_data"][2])

@app.route('/download', methods=['POST', 'GET'])
def download():
    if request.method=='POST':
        if 'user' in session:
            ukey = session['user']
        user_dict = session['user_dict']
        popu_decoded = jsonpickle.decode(user_dict[ukey]["population"])

        create_multi_xml(popu_decoded, user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2], ukey)

        db.child("users").child(ukey).set(user_dict[ukey]["db_data"])

        fig_url = create_figure(ukey, user_dict)

    return render_template("download.html", url=fig_url, user_dict=user_dict[ukey]["db_data"], done=True)

# # @app.route('/downloadpdf/<path:index_pop>', methods=['POST', 'GET'])
# # def downloadpdf(index_pop):
# # 	if 'user' in session:
# # 		ukey = session['user']
# # 	global user_dict
# # 	pdfpath = create_pdf(user_dict[ukey]["population"][int(index_pop)-1], user_dict[ukey]["db_data"][0], user_dict[ukey]["db_data"][1], user_dict[ukey]["db_data"][2], index_pop)

# 	return send_file(pdfpath, as_attachment=True)

@app.route('/datadmin', methods=['POST', 'GET'])
def data():
    users = db.child("users").get()

    user_count = 0
    x_all = []      # each user’s generation indices
    y_all = []      # each user’s normalized fitness per generation
    users_data = [] # metadata table

    for user in users.each():
        user_count += 1
        population_num = 4  # constant in your code

        # user.val()[5] is sum_fitness list
        raw_sum_fit = user.val()[5]  # list of integers (sum of ratings)
        sum_fit_pct = normalize_fitness(raw_sum_fit, population_num=population_num, max_rating=5)

        gen_list = list(range(1, len(sum_fit_pct) + 1))

        x_all.append(gen_list)
        y_all.append(sum_fit_pct)

        # users_data row: [key, scale, key, generation, instrument, age, experience, email]
        users_data.append([
            user.key(),   # nickname
            user.val()[0],  # scale
            user.val()[1],  # key
            user.val()[2],  # last generation
            user.val()[3],  # instrument
            user.val()[6],  # age
            user.val()[7],  # experience
            user.val()[8],  # email
        ])

    # If no users, just render empty
    if not x_all:
        return render_template(
            "data.html",
            users_data=[],
            epoch_mean=0,
            mean_x_axis=[],
            mean_y_axis=[],
            rolling_avg=[],
            pct_changes=[],
            hist_x=[],
            hist_counts=[]
        )

    # Build mean curve per generation index
    max_len = max(len(xs) for xs in x_all)
    mean_x_axis = list(range(1, max_len + 1))

    # collect values per generation position
    stacked = [[] for _ in range(max_len)]
    for xs, ys in zip(x_all, y_all):
        for idx, val in enumerate(ys):
            stacked[idx].append(val)

    mean_y_axis = [
        (sum(vals) / len(vals)) if vals else 0.0
        for vals in stacked
    ]

    # Rolling mean & percent change
    rolling_avg = rolling_mean(mean_y_axis, window=2)
    pct_changes = pct_change_percent(mean_y_axis)

    # Histogram of iterations per user (generations - 1)
    list_iteration = [row[3] - 1 for row in users_data]  # row[3] is generation
    hist_x, hist_counts = build_histogram(list_iteration)

    epoch_mean = sum(list_iteration) / len(list_iteration) if list_iteration else 0.0

    # We pass ready-to-plot data to template
    return render_template(
        "data.html",
        users_data=users_data,
        epoch_mean=epoch_mean,
        mean_x_axis=mean_x_axis,
        mean_y_axis=mean_y_axis,
        rolling_avg=rolling_avg,
        pct_changes=pct_changes,
        hist_x=hist_x,
        hist_counts=hist_counts
    )


@app.route('/tmp/uploads/<time_folder>/<generation_id>/<path:filename>')
def get_midi(time_folder, generation_id, filename):
    file_path = f"/tmp/uploads/{time_folder}/{generation_id}/{filename}"

    # Log every access (useful for Vercel debugging)
    print(f"[GET MIDI] Requested: {file_path}")

    # 1. File not found
    if not os.path.exists(file_path):
        print(f"[GET MIDI] File does NOT exist → {file_path}")
        # You can return JSON instead of HTML for clearer debugging on Vercel
        return jsonify({"error": "File not found", "path": file_path}), 404

    # 2. File exists, but Vercel fails to read it for some reason
    try:
        print(f"[GET MIDI] Sending file: {file_path}")
        return send_file(file_path, mimetype="audio/midi")
    except Exception as e:
        print("[GET MIDI] ERROR while sending file:", e)
        traceback.print_exc()

        # more detailed response while debugging
        return jsonify({
            "error": "Failed to send MIDI file",
            "exception": str(e),
            "path": file_path
        }), 500

def create_figure(ukey, user_dict) -> str:
    population_num = 4

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots()

    sum_fit = []
    for single_sum_fit in user_dict[ukey]["db_data"][5]:
        single_sum_fit = single_sum_fit/(population_num*5)*100
        sum_fit.append(single_sum_fit)

    gen_list = list(range(1, len(sum_fit) + 1))
    ax.plot(gen_list, sum_fit, 'o-', label=ukey)
    url = save_figure(ax, fig, ukey)
    return url

def save_figure(ax, fig, pathid) -> str:
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.xaxis.set_major_locator(mtick.MultipleLocator(1))
    ax.legend(loc='best')
    ax.set_title("Tingkat ketertarikan/fitness di setiap iterasi")
    ax.set_xlabel("Iterasi / Generasi-1")
    ax.set_ylabel("Presentase ketertarikan/fitness")
    plt.tight_layout()
    local_path = '/tmp/uploads/fig_' + pathid + '.jpg'
    fig.savefig(local_path, dpi=70)
    url = storage_service.upload_file(local_path)
    return url

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

def normalize_fitness(sum_fitnesses, population_num=4, max_rating=5):
    """Convert sum of ratings into percentage [0, 100]."""
    return [(fit / (population_num * max_rating)) * 100 for fit in sum_fitnesses]

def build_histogram(values):
    """
    Build histogram data: returns (sorted_labels, counts)
    like what you'd feed into a bar chart.
    """
    if not values:
        return [], []
    c = Counter(values)
    labels = sorted(c.keys())
    counts = [c[k] for k in labels]
    return labels, counts

# main driver function
if __name__ == '__main__':
    app.run(debug=True)
