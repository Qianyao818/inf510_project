# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 10:53:59 2019

@author: Qianyao
"""

import requests, time, csv, sqlite3, argparse, sys
from bs4 import BeautifulSoup

class movie:
    # is used to combine information about each movie and insert into database
    def __init__(self, movie_id, title, release_year, vote_average, rank):
        # initialize a new object with detail from one source
        self.movie_id = movie_id
        self.title = title
        self.release_year = release_year
        self.vote_average = vote_average
        self.rank = rank

    def __str__(self):
        t = str(self.movie_id) + " " + self.title + " " + str(self.release_year) + " " + str(
            self.vote_average) + " " + str(self.rank)
        return t

    def add_attribute(self, vote_count, genre_id1, genre_id2, genre_id3, budget, country):
        # add attributes from the other data source to the existing object
        self.vote_count = vote_count
        self.genre_id1 = genre_id1
        self.genre_id2 = genre_id2
        self.genre_id3 = genre_id3
        self.budget = budget
        self.country = country


def access_oscar_url(year, cursor, conn):
    # scrap one-year award data from the oscars website
    awards_list = []
    movie_awards_list = []
    movies_list = []
    url = "https://www.oscars.org/oscars/ceremonies/" + str(year)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    all_awards = soup.findAll('div', {"class": "view-grouping"})
    for val in all_awards:
        award = val.find('div', {"class": "view-grouping-header"}).text
        if award in ['Best Picture', 'Foreign Language Film']:
            awards_list.append(val)
    for val in awards_list:
        award = val.find('div', {"class": "view-grouping-header"}).text
        movies = val.findAll('h4', {"class": "field-content"})
        for i in range(len(movies)):
            if i == 0:
                movie_line = (year, award, "winner", movies[i].text)
            else:
                movie_line = (year, award, "nominee", movies[i].text)
            # print(movie_line)
            new_m = add_award(movie_line, cursor, conn, "remote")
            #print('hi', new_m)
            if new_m is not None:
                movies_list.append(new_m)
            #print(movie_line)
            movie_awards_list.append(movie_line)
    print(len(movies_list))
    t = (movie_awards_list, movies_list)
    return t


def scarp_oscar(lyear, cursor, conn):
    # scarp oscar award data from 1988 to 2017
    movie_awards_list = []
    movie_list = []
    year = 1988
    while year <= int(lyear):
        t = access_oscar_url(year, cursor, conn)
        #print(year)
        movie_awards_list.extend(t[0])
        #print(len(access_oscar_url(year, cursor, conn)[1]))
        movie_list.extend(t[1])
        year += 1
        time.sleep(10)
    write_csv(movie_awards_list, "oscar.csv")
    write_movies(movie_list, "award_movies.csv")

# get_awards()


def get_genre(cursor, conn):
    # get genre types data from the API of TMDB
    url = 'https://api.themoviedb.org/3/genre/movie/list?'
    params = {'api_key': '2e765780e97748dec75dde38f03e4384'}
    json_response = requests.get(url, params=params)
    genres = json_response.json()['genres']
    genre_list = []
    for genre in genres:
        id = genre['id']
        name = genre['name']
        g = (id, name)
        add_genre(g, cursor, conn)
        genre_list.append(g)
    write_csv(genre_list, "genre.csv")


def top_rated_movies(num, cursor, conn):
    # get 250 top rated movies data from the API of TMDB
    url = 'https://api.themoviedb.org/3/movie/top_rated?'
    page = 1
    i = 1
    movie_list = []
    while i <= int(num):
        #print(i)
        params = {'api_key': '2e765780e97748dec75dde38f03e4384', 'page': page}
        json_response = requests.get(url, params=params)
        movies = json_response.json()['results']
        for val in movies:
            year = int(val['release_date'][0:4])
            if year >= 1988 and year <= 2017:
                movie_id = val['id']
                title = val['title']
                release_year = year
                vote_average = val['vote_average']
                rank = i
                m = movie(movie_id, title, release_year, vote_average, rank)
                if i <= int(num):
                    i += 1
                    movie_detail(m, cursor, conn)
                    movie_list.append(m)
                    #print(m)
        page += 1
        time.sleep(2)
    write_movies(movie_list, "top_rated_movies.csv")


def movie_detail(m, cursor, conn):
    # get details about each movie by movie id from the API of TMDB
    url = 'https://api.themoviedb.org/3/movie/' + str(m.movie_id) + '?'
    params = {'api_key': '2e765780e97748dec75dde38f03e4384'}
    json_response = requests.get(url, params=params)
    detail = json_response.json()
    vote_count = detail['vote_count']
    length = len(detail['genres'])
    if length == 0:
        genre_id1 = 0
        genre_id2 = 0
        genre_id3 = 0
    elif length == 1:
        genre_id1 = detail['genres'][0]['id']
        genre_id2 = 0
        genre_id3 = 0
    elif length == 2:
        genre_id1 = detail['genres'][0]['id']
        genre_id2 = detail['genres'][1]['id']
        genre_id3 = 0
    else:
        genre_id1 = detail['genres'][0]['id']
        genre_id2 = detail['genres'][1]['id']
        genre_id3 = detail['genres'][2]['id']
    budget = detail['budget']
    if len(detail['production_countries']) < 1:
        country = "No"
    else:
        country = detail['production_countries'][0]['iso_3166_1']
    m.add_attribute(vote_count, genre_id1, genre_id2, genre_id3, budget, country)
    add_movie(m, cursor, conn)
    print(m)
    time.sleep(1)


def search_movie(m):
    # get general information about movie by searching title from the API od TMDB
    url = 'https://api.themoviedb.org/3/search/movie?'
    params = {'api_key': '2e765780e97748dec75dde38f03e4384', 'query': m[3]}
    json_response = requests.get(url, params=params)
    new_m = None
    try:
        movies = json_response.json()['results']
    except KeyError:
        None
    else:
        for val in movies:
            title = val['title']
            try:
                year = int(val['release_date'][0:4])
            except ValueError:
                year = int(m[0])
            except KeyError:
                year = int(m[0])
            if title == m[3] and year in [int(m[0]) - 1, int(m[0])]:
                movie_id = val['id']
                title = title
                release_year = year
                vote_average = val['vote_average']
                rank = 0
                if vote_average == 0:
                    continue
                else:
                    new_m = movie(movie_id, title, release_year, vote_average, rank)
                    # print(new_m)
    return new_m


def get_country_num(lyear, cursor, conn):
    # get number of produced movies each country each year from 1988 to 2017
    year = 1988
    country_num_list = []
    while year <= int(lyear):
        #print(year)
        url = 'https://api.uis.unesco.org/sdmx/data/UNESCO,FF,1.0/NB.FF...NAT.._T._T._T.PROD.'
        params = {'startPeriod': year, 'endPeriod': year, 'format': 'sdmx-json', 'locale': 'en',
                  'subscription-key': '3a08d08184c04bf387d487b854962df1'}
        json_response = requests.get(url, params=params)
        country_num = json_response.json()
        for i in range(len(country_num['dataSets'][0]['series'])):
            num = country_num['dataSets'][0]['series']['0:0:' + str(i) + ':0:0:0:0:0:0:0:0']['observations']['0'][0]
            # length = len(number['dataSets'][0]['series'])
            country = country_num['structure']['dimensions']['series'][2]['values'][i]['id']
            # print(len(number['structure']['dimensions']['series'][2]['values']))
            # print(num,country)
            country_num_year = (country, num, year)
            add_country_num(country_num_year, cursor, conn)
            country_num_list.append(country_num_year)
        year += 1
    write_csv(country_num_list, "country.csv")


def create_table(cursor):
    cursor.execute('''DROP TABLE IF EXISTS Movies''')
    cursor.execute('''DROP TABLE IF EXISTS AwardType''')
    cursor.execute('''DROP TABLE IF EXISTS Country''')
    cursor.execute('''DROP TABLE IF EXISTS Award''')
    cursor.execute('''DROP TABLE IF EXISTS Genre''')
    cursor.execute('''DROP TABLE IF EXISTS Location''')
    cursor.execute('''CREATE TABLE Movies(id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, title TEXT,
    release_year INTEGER, vote_average REAL, rank INTEGER, vote_count INTEGER, genre_id1 INTEGER, genre_id2 INTEGER,
    genre_id3 INTEGER, budget REAL, country INTEGER)''')
    cursor.execute('''CREATE TABLE AwardType(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT)''')
    cursor.execute('''CREATE TABLE Country(id INTEGER PRIMARY KEY AUTOINCREMENT, country_id INTEGER, N1988 INTEGER, N1989 INTEGER,
    N1990 INTEGER, N1991 INTEGER, N1992 INTEGER, N1993 INTEGER, N1994 INTEGER, N1995 INTEGER, N1996 INTEGER,
    N1997 INTEGER, N1998 INTEGER, N1999 INTEGER, N2000 INTEGER, N2001 INTEGER, N2002 INTEGER, N2003 INTEGER,
    N2004 INTEGER, N2005 INTEGER, N2006 INTEGER, N2007 INTEGER, N2008 INTEGER, N2009 INTEGER, N2010 INTEGER,
    N2011 INTEGER, N2012 INTEGER, N2013 INTEGER, N2014 INTEGER, N2015 INTEGER, N2016 INTEGER, N2017 INTEGER)''')
    cursor.execute('''CREATE TABLE Award(id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, type INTEGER,
    year INTEGER)''')
    cursor.execute('''CREATE TABLE Genre(id INTEGER PRIMARY KEY AUTOINCREMENT, genre_id INTEGER, name TEXT)''')
    cursor.execute('''CREATE TABLE Location(id INTEGER PRIMARY KEY AUTOINCREMENT, country_name TEXT,  iso_2 INTEGER, 
        iso_3 INTEGER, long REAL, lat REAL)''')


def add_movie(m, cursor, conn):
    # insert movie information to database
    cursor.execute('SELECT * FROM Movies WHERE (movie_id=? or title=?)', (m.movie_id, m.title))
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute('SELECT ID FROM Location WHERE iso_2 = ?', (m.country,))
        entry = cursor.fetchone()
        if entry is None:
            #print(m.country)
            country_id = 0
        else:
            country_id = entry[0]
        cursor.execute(
            'INSERT INTO Movies (movie_id, title, release_year, vote_average, rank, vote_count, genre_id1, genre_id2, genre_id3, budget, country) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (m.movie_id, m.title, m.release_year, m.vote_average, m.rank, m.vote_count, m.genre_id1, m.genre_id2,
            m.genre_id3, m.budget, country_id))
    conn.commit()


def add_award_type(cursor, conn):
    # insert award type to database
    cursor.execute('INSERT INTO AwardType (name, type) VALUES ("Best Picture","winner")')
    cursor.execute('INSERT INTO AwardType (name, type) VALUES ("Best Picture","nominee")')
    cursor.execute('INSERT INTO AwardType (name, type) VALUES ("Foreign Language Film","winner")')
    cursor.execute('INSERT INTO AwardType (name, type) VALUES ("Foreign Language Film","nominee")')
    conn.commit()


def add_genre(genre, cursor, conn):
    # insert genre type to database
    cursor.execute('INSERT INTO Genre (genre_id, name) VALUES (?,?)', (genre[0], genre[1]))
    conn.commit()


def add_country_num(val, cursor, conn):
    # insert number of produced movies to database
    cursor.execute('SELECT ID FROM Location WHERE (iso_2=?)', (val[0],))
    entry = cursor.fetchone()
    num = int(val[1])
    year = str(val[2])
    if entry is not None:
        country_id = int(entry[0])
        cursor.execute('SELECT * FROM Country WHERE (country_id=?)', (country_id,))
        entry = cursor.fetchone()
        if entry is None:
            cursor.execute('INSERT INTO Country (country_id, N' + year + ') VALUES (?,?)', (country_id, num))
            conn.commit()
        else:
            sql = 'UPDATE Country SET N' + year + '=? WHERE (country_id=?)'
            cursor.execute(sql, (num, country_id))
            conn.commit()
    # print(country_name)

    #print("country added")


def add_award(m, cursor, conn, source):
    # insert award information to database
    cursor.execute('SELECT ID FROM Movies WHERE (title=?)', (m[3],))
    entry = cursor.fetchone()
    new_m = None
    if entry is None and source == 'remote':
        new_m = search_movie(m)
        if new_m is not None:
            movie_detail(new_m, cursor, conn)
            cursor.execute('SELECT ID FROM Movies WHERE (title=?)', (m[3],))
            entry = cursor.fetchone()
    if entry is not None:
        movie_id = int(entry[0])
        cursor.execute('SELECT ID FROM AwardType WHERE (name=? and type=?)', (m[1], m[2]))
        entry = cursor.fetchone()
        award_type = int(entry[0])
        cursor.execute('INSERT INTO Award (movie_id, type, year) VALUES (?,?,?)', (movie_id, award_type, m[0]))
        conn.commit()
    return new_m


def remote(year1, year2, num):
    # grab data from remote source
    print("Processing begin.")
    conn = sqlite3.connect('../data/movies.db')
    cursor = conn.cursor()
    create_table(cursor)

    geocoding(cursor, "geocoding.csv", conn)

    add_award_type(cursor, conn)
    print("Award type data is added.")

    get_genre(cursor, conn)
    print("Genre type data is added.")

    get_country_num(year1, cursor, conn)
    print("Movie number by country data is added.")

    top_rated_movies(num,cursor, conn)
    print("Top rated movies data is added.")

    scarp_oscar(year2, cursor, conn)
    print("Awarded movies data is added.")
    print("Awarded movies by year data is added.")

    conn.commit()
    conn.close()
    print("Data processing has been completed.")


def read_csv(csv_file):
    return_list = []
    try:
        with open("../data/"+csv_file, 'r') as csvfile:
            lines = csv.reader(csvfile, delimiter=';')
            for line in lines:
                return_list.append(line)
    except FileNotFoundError:
        print(csv_file, "is not exist")
        sys.exit()
    else:
        return return_list


def read_movies(csv_file):
    return_list = []
    try:
        with open("../data/"+csv_file, 'r') as csvfile:
            lines = csv.reader(csvfile, delimiter=';')
            for line in lines:
                m = movie(line[0], line[1], line[2], line[3], line[4])
                m.add_attribute(line[5], line[6], line[7], line[8], line[9], line[10])
                return_list.append(m)
    except FileNotFoundError:
        print(csv_file, "is not exist")
        sys.exit()
    else:
        return return_list


def local():
    # grab data from local source
    print("Processing begin.")
    conn = sqlite3.connect('../data/movies_local.db')
    cursor = conn.cursor()
    create_table(cursor)

    geocoding(cursor, "geocoding.csv", conn)

    add_award_type(cursor, conn)
    print("Award type data is added.")


    genre_list = read_csv("genre.csv")
    for genre in genre_list:
        add_genre(genre, cursor, conn)
    print("Genre type data is added.")


    country_num_list = read_csv("country.csv")
    for country in country_num_list:
        add_country_num(country, cursor, conn)
    print("Movie number by country data is added.")

    movie_list = read_movies("top_rated_movies.csv")
    for m in movie_list:
        add_movie(m, cursor, conn)
    print("Top rated movies data is added.")

    movie_awards_list = read_movies("award_movies.csv")
    for m in movie_awards_list:
        add_movie(m, cursor, conn)
    print("Awarded movies data is added.")

    award_list = read_csv("oscar.csv")
    for award in award_list:
        add_award(award, cursor, conn, "local")
    print("Awarded movies by year data is added.")

    conn.commit()
    conn.close()

    print("Data processing has been completed.")


def write_csv(csv_list, csv_file):
    with open("../data/"+csv_file, 'w', newline='') as csvfile:
        write_row = csv.writer(csvfile, delimiter=';')
        for line in csv_list:
            write_row.writerow(line)


def write_movies(movie_list, movie_csv):
    with open("../data/"+movie_csv, 'w', newline='') as csvfile:
        write_row = csv.writer(csvfile, delimiter=';')
        for m in movie_list:
            line = (m.movie_id, m.title, m.release_year, m.vote_average, m.rank, m.vote_count, m.genre_id1, m.genre_id2, m.genre_id3, m.budget, m.country)
            write_row.writerow(line)


def geocoding(cursor, csvfile, conn):
    # get geographic information about each country
    loc = read_csv(csvfile)
    for line in loc:
        cursor.execute('INSERT INTO Location (country_name, iso_2, iso_3, long, lat) VALUES (?,?,?,?,?)', (line[0], line[1], line[2], line[4], line[3]))
        conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-source", choices=["local", "remote", "test"], help="where data should be gotten from")
    args = parser.parse_args(sys.argv[1:])

    option = args.source

    if option == "local":
        local()
    elif option == "test":
        remote(1993, 1993, 30)
    else:
        remote(2017, 2017, 250)


if __name__ == "__main__":
    main()
