import requests
import json
import secrets
from bs4 import BeautifulSoup
import sys
import codecs
import sqlite3
import plotly.plotly as py
import plotly.graph_objs as go

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

OMDB_KEY = secrets.secret_key

DB_NAME = 'movies.sqlite'

CACHE_FNAME = 'movies-cache.json'
try:
	cache_file = open(CACHE_FNAME, 'r')
	MOVIE_CACHE_DICT = json.loads(cache_file.read())
	cache_file.close()
except:
	MOVIE_CACHE_DICT = {}

class Movie():

	def __init__(self, title, x_val, y_val, vis_type):
		self.x_val = x_val
		self.y_val = y_val
		self.title = title
		self.vis_type = vis_type

	def __str__(self):
		if self.vis_type == 1:
			return self.title + " (Metascore: " + str(self.x_val) + ", User Score: " + str(self.y_val) + ")"
		elif self.vis_type == 2:
			return self.title + " (Metascore: " + str(self.x_val) + ", Run Time: " + str(self.y_val) + " min)"
		elif self.vis_type == 3:
			return self.title + " (Metascore: " + str(self.x_val) + ", Box Office Gross: $" + str(self.y_val) + ")"
		elif self.vis_type == 4:
			return self.title + " (User Score: " + str(self.x_val) + ", Run Time: " + str(self.y_val) + " min)"
		elif self.vis_type == 5:
			return self.title + " (User Score: " + str(self.x_val) + ", Box Office Gross: $" + str(self.y_val) + ")"


def get_metacritic_data():
	base_url = 'http://www.metacritic.com'
	list_url = base_url + '/browse/movies/score/metascore/all/filtered'
	user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'}
	movies = []
	movie_scores = []
	if list_url in MOVIE_CACHE_DICT:
		movies = MOVIE_CACHE_DICT[list_url]
	else:
		html = requests.get(list_url, headers=user_agent).text
		soup = BeautifulSoup(html, 'html.parser')
		movies_list = soup.find_all(class_='title')
		
		for elem in movies_list:
			title = elem.find('a').string
			movie_url_extension = elem.find('a').attrs['href']
			movie_url = base_url + movie_url_extension
			success = False

			# Random errors in html rendering were causing data collection to unpredictably fail
			# when attempting to navigate to the page containing critical data. This while loop
			# allows the program to attempt to get the data againif it fails the first time.

			while not success:

				try:

					movie_html = requests.get(movie_url, headers=user_agent).text

					movie_soup = BeautifulSoup(movie_html, 'html.parser')
					links = movie_soup.find_all(class_='metascore_anchor')
				
					critic_url_extension = links[0].attrs['href']
					critic_url = base_url + critic_url_extension
					critic_html = requests.get(critic_url, headers=user_agent).text
					
					critic_soup = BeautifulSoup(critic_html, 'html.parser')
					critic_summary = critic_soup.find(class_='simple_summary')
					metascore = critic_summary.find(class_='metascore_w').string
					num_critics = critic_summary.find(class_='based_on').string.split()[2]
					user_url_extension = links[1].attrs['href']
					user_url = base_url + user_url_extension

					user_html = requests.get(user_url, headers=user_agent).text
				
					user_soup = BeautifulSoup(user_html, 'html.parser')
					user_summary = user_soup.find(class_='simple_summary')
					user_score = user_summary.find(class_='metascore_w').string
					num_users = user_summary.find(class_='based_on').string.split()[2]
					success = True
				except:
					continue
			if metascore == user_score:
				user_score == 0
				num_users == 0
			movies.append((title, metascore, num_critics, user_score, num_users))

		MOVIE_CACHE_DICT[list_url] = movies
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(MOVIE_CACHE_DICT))
		cache_file.close()

	return movies

def get_omdb_data(title):
	base_url = 'http://www.omdbapi.com'
	params = {}
	params['apikey'] = OMDB_KEY
	params['t'] = title
	unique_ident = "{}-{}".format(base_url, params['t'])
	if unique_ident in MOVIE_CACHE_DICT:
		omdb_dict = MOVIE_CACHE_DICT[unique_ident]
	else:
		response = requests.get(base_url, params=params)
		omdb_dict = json.loads(response.text)
		MOVIE_CACHE_DICT[unique_ident] = omdb_dict
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(MOVIE_CACHE_DICT))
		cache_file.close()
	try:
		release_year = omdb_dict['Year']
	except:
		release_year = 'N/A'
	try:
		rating = omdb_dict['Rated']
	except:
		rating = 'N/A'
	try:
		runtime = omdb_dict['Runtime'].split()[0]
	except:
		runtime = '0'
	try:
		director = omdb_dict['Director']
	except:
		director = 'N/A'
	try:
		if omdb_dict['BoxOffice'] == 'N/A':
			gross = '0'
		else:
			gross = omdb_dict['BoxOffice'].replace('$', '').replace(',', '')
	except:
		gross = '0'
	return (title, release_year, rating, runtime, director, gross)

def init_db():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	statement = '''
		DROP TABLE IF EXISTS MovieInfo
	'''
	cur.execute(statement)
	conn.commit()

	statement = '''
		DROP TABLE IF EXISTS MovieScores
	'''
	cur.execute(statement)
	conn.commit()

	statement = '''
		CREATE TABLE 'MovieScores' (
			'MovieId' INTEGER PRIMARY KEY,
			'Metascore' INTEGER,
			'NumCritics' INTEGER,
			'UserScore' REAL,
			'NumUsers' INTEGER
			);
	'''
	cur.execute(statement)
	conn.commit()

	statement = '''
		CREATE TABLE 'MovieInfo' (
			'Id' INTEGER PRIMARY KEY,
			'Title' TEXT,
			'ReleaseYear' TEXT,
			'Rating' TEXT,
			'RunTime' INTEGER,
			'Director' TEXT,
			'Gross' INTEGER
			);
	'''
	cur.execute(statement)
	conn.commit()

	conn.close()

def insert_data():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	top_movies = get_metacritic_data()
	for movie in top_movies:
		movie_info = get_omdb_data(movie[0])

		insert = '''
			INSERT INTO MovieInfo (Title, ReleaseYear, Rating, RunTime, Director, Gross)
			VALUES (?, ?, ?, ?, ?, ?)
		'''

		cur.execute(insert, movie_info)
		conn.commit()

		insert = '''
			INSERT INTO MovieScores 
			VALUES (
				(SELECT Id
				FROM MovieInfo
				WHERE Title=?),
				?, ?, ?, ?)
		'''
		cur.execute(insert, movie)
		conn.commit()

		# When no user score is available, the critic score is improperly substituted
		# This update statement resolves thi for data visualization purposes

		update = '''
			UPDATE MovieScores
			SET UserScore=0
			WHERE UserScore>10
		'''

		cur.execute(update)
		conn.commit()

	conn.close()

def plot_critics_v_users():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	q = '''
		SELECT i.Title, s.Metascore, s.UserScore
		FROM MovieInfo AS i
		JOIN MovieScores AS s
			ON s.MovieId=i.Id
	'''
	movies = []

	titles = []
	metascores = []
	user_scores = []

	for row in cur.execute(q):
		movies.append(Movie(*row, 1))

	for movie in movies:
		titles.append(movie.__str__())
		metascores.append(movie.x_val)
		user_scores.append(movie.y_val)

	conn.close()

	data = [
		go.Scatter(
			x = metascores,
			y = user_scores,
			mode = 'markers',
			text = titles
		)
	]
	layout = go.Layout(
		title = 'Top 100 Movies (Metascore vs. User Score) (0 Where Data Unavailable)'
	)
	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, validate=False, filename="metascore-vs-user-score")

def plot_critics_v_boxoffice():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	q = '''
		SELECT i.Title, s.Metascore, i.Gross
		FROM MovieInfo AS i
		JOIN MovieScores AS s
			ON s.MovieId=i.Id
	'''
	movies = []

	titles = []
	metascores = []
	gross_list = []

	for row in cur.execute(q):
		movies.append(Movie(*row, 3))

	for movie in movies:
		titles.append(movie.__str__())
		metascores.append(movie.x_val)
		gross_list.append(movie.y_val)

	conn.close()

	data = [
		go.Scatter(
			x = metascores,
			y = gross_list,
			mode = 'markers',
			text = titles
		)
	]
	layout = go.Layout(
		title = "Top 100 Movies (Metascore vs. Box Office) (0 Where Data Unavailable)"
	)
	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, validate=False, filename="metascore-vs-boxoffice")

def plot_critics_v_runtime():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	q = '''
		SELECT i.Title, s.Metascore, i.RunTime
		FROM MovieInfo AS i
		JOIN MovieScores AS s
			ON s.MovieId=i.Id
	'''
	movies = []

	titles = []
	metascores = []
	runtimes = []

	for row in cur.execute(q):
		movies.append(Movie(*row, 2))

	for movie in movies:
		titles.append(movie.__str__())
		metascores.append(movie.x_val)
		runtimes.append(movie.y_val)

	conn.close()

	data = [
		go.Scatter(
			x = metascores,
			y = runtimes,
			mode = 'markers',
			text = titles
		)
	]
	layout = go.Layout(
		title = "Top 100 Movies (Metascore vs. Run Time) (0 Where Data Unavailable)"
	)
	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, validate=False, filename="metascore-vs-runtime")

def plot_users_v_boxoffice():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	q = '''
		SELECT i.Title, s.UserScore, i.Gross
		FROM MovieInfo AS i
		JOIN MovieScores AS s
			ON s.MovieId=i.Id
	'''
	movies = []

	titles = []
	user_scores = []
	gross_list = []

	for row in cur.execute(q):
		movies.append(Movie(*row, 5))

	for movie in movies:
		titles.append(movie.__str__())
		user_scores.append(movie.x_val)
		gross_list.append(movie.y_val)

	conn.close()

	data = [
		go.Scatter(
			x = user_scores,
			y = gross_list,
			mode = 'markers',
			text = titles
		)
	]
	layout = go.Layout(
		title = "Top 100 Movies (User Score vs. Box Office) (0 Where Data Unavailable)"
	)
	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, validate=False, filename="userscore-vs-boxoffice")

def plot_users_v_runtime():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	q = '''
		SELECT i.Title, s.UserScore, i.RunTime
		FROM MovieInfo AS i
		JOIN MovieScores AS s
			ON s.MovieId=i.Id
	'''
	movies = []

	titles = []
	user_scores = []
	runtimes = []

	for row in cur.execute(q):
		movies.append(Movie(*row, 4))

	for movie in movies:
		titles.append(movie.__str__())
		user_scores.append(movie.x_val)
		runtimes.append(movie.y_val)

	conn.close()

	data = [
		go.Scatter(
			x = user_scores,
			y = runtimes,
			mode = 'markers',
			text = titles
		)
	]
	layout = go.Layout(
		title = "Top 100 Movies (User Score vs. Run Time) (0 Where Data Unavailable)"
	)
	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, validate=False, filename="userscore-vs-runtime")

def interactive_prompt():
	print("Welcome!")
	print("This program can show you data about the top 100 movies of all time according to Metacritic.com")
	print("How would you like the data visualized?")
	print("1) Crtic Score vs. User Score")
	print("2) Critic Score vs. Box Office Gross")
	print("3) Critic Score vs. Run Time")
	print("4) User Score vs. Box Office Gross")
	print("5) User Score vs. Run Time")
	user_choice = input("Enter your choice (1-5), or type 'exit' to end. Additionally, you can type 'options' to see options again: ")
	while user_choice != "exit":
		if user_choice == '1':
			plot_critics_v_users()
		elif user_choice == '2':
			plot_critics_v_boxoffice()
		elif user_choice == '3':
			plot_critics_v_runtime()
		elif user_choice == '4':
			plot_users_v_boxoffice()
		elif user_choice == '5':
			plot_users_v_runtime()
		elif user_choice == 'options': 
			print("How would you like the data visualized?")
			print("1) Crtic Score vs. User Score")
			print("2) Critic Score vs. Box Office Gross")
			print("3) Critic Score vs. Run Time")
			print("4) User Score vs. Box Office Gross")
			print("5) User Score vs. Run Time")
		else:
			print("Invalid command: " + user_choice)
		user_choice = input("Enter your choice (1-5), or type 'exit' to end. Additionally, you can type 'options' to see options again: ")

	print("Goodbye!")



if __name__=="__main__":
	interactive_prompt()