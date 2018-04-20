import unittest
from movies import *

class TestClass(unittest.TestCase):

	def test_movie(self):
		movie = Movie('Citizen Kane', 100, 8.4, 1)
		self.assertEqual(movie.title, 'Citizen Kane')
		self.assertEqual(movie.x_val, 100)
		self.assertEqual(movie.y_val, 8.4)
		self.assertEqual(movie.__str__(), "Citizen Kane (Metascore: 100, User Score: 8.4)")

		movie = Movie('Boyhood', 7.7, 165, 4)
		self.assertEqual(movie.title, 'Boyhood')
		self.assertEqual(movie.x_val, 7.7)
		self.assertEqual(movie.y_val, 165)
		self.assertEqual(movie.__str__(), "Boyhood (User Score: 7.7, Run Time: 165 min)")
	

class TestDataCollection(unittest.TestCase):

	def test_get_metacritic_data(self):
		movies = get_metacritic_data()
		self.assertEqual(len(movies), 100)
		self.assertEqual(movies[0][0], 'Citizen Kane')
		self.assertEqual(movies[0][1], '100')
		self.assertEqual(movies[0][2], '18')
		self.assertEqual(movies[0][3], '8.4')
		self.assertEqual(movies[0][4], '126')

	def test_get_omdb_data(self):
		movie = get_omdb_data('Boyhood')
		self.assertEqual(movie[0], 'Boyhood')
		self.assertEqual(movie[1], '2014')
		self.assertEqual(movie[2], 'R')
		self.assertEqual(movie[3], '165')
		self.assertEqual(movie[4], 'Richard Linklater')
		self.assertEqual(movie[5], '18859617')


class TestDatabase(unittest.TestCase):

	def test_movie_scores_table(self):
		conn = sqlite3.connect(DB_NAME)
		cur = conn.cursor()

		statement = '''
			SELECT *
			FROM MovieScores
		'''

		results = cur.execute(statement)
		results_list = results.fetchall()
		self.assertEqual(len(results_list), 100)

		statement = '''
			SELECT *
			FROM MovieScores
			WHERE Metascore=100
		'''

		results = cur.execute(statement)
		results_list = results.fetchall()
		self.assertEqual(len(results_list), 6)
		self.assertEqual(results_list[4][4], 1979)

	def test_movie_info_table(self):
		conn = sqlite3.connect(DB_NAME)
		cur = conn.cursor()

		statement = '''
			SELECT *
			FROM MovieInfo
		'''

		results = cur.execute(statement)
		results_list = results.fetchall()
		self.assertEqual(len(results_list), 100)

		statement = '''
			SELECT *
			FROM MovieInfo
			WHERE Rating="PG"
		'''

		results = cur.execute(statement)
		results_list = results.fetchall()
		self.assertEqual(len(results_list), 11)
		self.assertEqual(results_list[2][1], 'Casablanca')

	def test_connection(self):
		conn = sqlite3.connect(DB_NAME)
		cur = conn.cursor()

		statement = '''
			SELECT MovieInfo.Title, MovieScores.Metascore
			FROM MovieInfo
				JOIN MovieScores
				ON MovieInfo.Id=MovieScores.MovieId
			WHERE Title='Amour'
		'''

		results = cur.execute(statement)
		results_list = results.fetchall()
		self.assertEqual(len(results_list), 1)
		self.assertEqual(results_list[0][1], 94)


unittest.main()