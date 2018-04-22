import sqlite3
from requests import get
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
import re
import math
import os
from config import *

#Interface with SQL
def run_query(DB, q):
    with sqlite3.connect(DB) as conn:
        return pd.read_sql(q,conn)

def run_command(DB, c):
    with sqlite3.connect(DB) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.isolation_level = None
        conn.execute(c)
        
def run_inserts(DB, c, values):
    with sqlite3.connect(DB) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.isolation_level = None
        conn.execute(c, values) 
		
		
#Studios scraper, only one page
def scrape_studios(DB='anime.db'):

    start_time = time.time()
    insert_query = '''
    INSERT OR IGNORE INTO studios(
        studio_id,  
        studio_name
        ) 
    VALUES (?, ?)
    '''

    #Create a special entry for unknown studios
    insert_special = '''
    INSERT OR IGNORE INTO studios(
        studio_id,
        studio_name
        )
    VALUES (9999, 'Unknown')
    '''

    run_command(DB, insert_special)

    #Makes the request
    url = 'https://myanimelist.net/anime/producer'
    headers = {
        "User-Agent": "mal review scraper for research."
    }

    #Handle timeouts
    try:
        response = get(url, headers=headers, timeout = 10)
    except:
        print('Request timeout')

    #Dump failed queries into a list        
    failed_queries = []

    #Creates the soup object    
    html_soup = BeautifulSoup(response.text, 'html.parser')
    total_studios = len(html_soup.find_all('a', class_ = 'genre-name-link'))
    for i in range(total_studios):
        result = html_soup.find_all('a', class_ = 'genre-name-link')[i].attrs['href'].replace('/anime/producer/', '').split('/', 1)
        studio_id = result[0]
        studio_name = result[1]

        #Write into SQL database
        try:
            run_inserts(DB, insert_query,(
                int(studio_id), studio_name)
            )
        except:
            print('Insert Failed {}'.format(studio_name))
            failed_queries.append(studio_name)
            pass

        #Provide stats for monitoring
        os.system('cls' if os.name == 'nt' else 'clear')
        print('Scraping studio data')
        print('Scraping: {}'.format(url))
        print('Inserted into database: \'{}\''.format(studio_name)) 
        

    print('Scrape Complete')
    print('Processing time: {} seconds'.format(time.time() - start_time))
	
#Tags scraper, only one page
def scrape_tags(DB='anime.db'):
    DB = 'anime.db'
    start_time = time.time()

    insert_query = '''
    INSERT OR IGNORE INTO tags(
        tag_id,  
        tag_name
        ) 
    VALUES (?, ?)
    '''

    #Makes the request
    url = 'https://myanimelist.net/anime.php'
    headers = {
        "User-Agent": "mal review scraper for research."
    }

    #Handle timeouts
    try:
        response = get(url, headers=headers, timeout = 10)
    except:
        print('Request timeout')

    #Dump failed queries into a list
    failed_queries = []

    #Create the soup object
    html_soup = BeautifulSoup(response.text, 'html.parser')
    total_tags = len(html_soup.find_all('div', class_ = 'genre-link')[0].find_all('a', class_='genre-name-link'))   
    for i in range(total_tags):
        result = html_soup.find_all('a', class_='genre-name-link')[i].attrs['href'].replace('/anime/genre/', '').split('/', 1)
        tag_id = result[0]
        tag_name = result[1]
        #Write into SQL database
        try:
            run_inserts(DB, insert_query,(
                int(tag_id), tag_name)
            )
        except Exception as e:
            print('Failed to insert into animes for tag_id: {0}, {1}'.format(tag_id, e))
            failed_queries.append(tag_id)
            pass

        #Provide stats for monitoring
        os.system('cls' if os.name == 'nt' else 'clear')
        print('Scraping tags data')
        print('Scraping: {}'.format(url))
        print('Inserted into database: \'{}\''.format(tag_name)) 
        
		
    print('Scrape Complete')
    print('Processing time: {} seconds'.format(time.time() - start_time))

#Animes, anime_tags scraper
def scrape_animes(DB='anime.db', sleep_min=9, sleep_max=18):
    start_time = time.time()
    
    insert_query1 = '''
    INSERT OR IGNORE INTO animes(
        anime_id,
        studio_id,
        anime_name,        
        episodes_total,
        source_material,
        air_date,
        overall_rating,
        members,
        synopsis
        )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    insert_query2 = '''
    INSERT OR IGNORE INTO anime_tags(
        anime_id,
        tag_id
        ) 
    VALUES (?, ?)
    '''

    #Makes the initial request, only once
    url = 'https://myanimelist.net/anime.php'
    headers = {
        "User-Agent": "mal review scraper for research."
    }
    try:
        response = get(url, headers=headers, timeout = 10)
    except:
        print('Request timeout')

    #Create the soup object to calculate the number of tags
    html_soup_initial = BeautifulSoup(response.text, 'html.parser')
    total_tags = len(html_soup_initial.find_all('div', class_ = 'genre-link')[0].find_all('a', class_='genre-name-link')) 


    requests = 0
    #Start loop for each tag
    for j in range(total_tags):
        tag_details = html_soup_initial.find_all('a', class_='genre-name-link')[j]
        total_animes = int(tag_details.text.split('(')[1].replace(')', '').replace(',', ''))
        link_value = tag_details.attrs['href'].replace('/anime/genre/', '').split('/')[0]

        #Start loop for each page within the tag
        for i in range(math.ceil(total_animes/100)):

            url = 'https://myanimelist.net/anime/genre/{0}/?page={1}'.format(link_value, i+1)
            headers = {
                "User-Agent": "mal review scraper for research."
            }
            print('Scraping: {}'.format(url))


            #Handle timeouts
            try:
                response = get(url, headers=headers, timeout = 10)
            except:
                print('Request timeout')
                pass

            if response.status_code != 200:
                print('Request: {}; Status code: {}'.format(requests, response.status_code))
                pass

            #Creates the soup object    
            html_soup = BeautifulSoup(response.text, 'html.parser')
            containers = html_soup.find_all('div', class_='seasonal-anime')
            for container in containers:

                #Primary key for 'animes'
                anime_id = container.find('div', class_='genres js-genre').attrs['id']

                #Foreign key for 'animes', use 9999 for unknown studios
                try:
                    studio_id = container.find('span', class_='producer').find('a').attrs['href'].replace('/anime/producer/', '').split('/')[0]
                except:
                    studio_id = 9999

                #Anime info
                anime_name = container.find('a', class_='link-title').text            
                episodes_total = container.find('div', class_='eps').text.strip().split(' ')[0]
                source_material = container.find('span', class_='source').text
                air_date = container.find('span', class_='remain-time').text.strip()
                members = container.find('span', class_='member').text.strip().replace(',', '')
                synopsis = container.find('span', class_='preline').text.strip().replace('\n', '').replace('\r', '')
                try:
                    overall_rating = float(container.find('span', class_='score').text.strip())
                except:
                    overall_rating = 'null'

                #Write into SQL database, table: animes
                try:
                    run_inserts(DB,
                        insert_query1,(
                            int(anime_id), int(studio_id), anime_name, episodes_total, source_material, \
                            air_date, overall_rating, \
                            int(members), synopsis 
                        )
                    )
                except Exception as e:
                    print('Failed to insert into animes for anime_id: {0}, {1}'.format(anime_id, e))
                    pass

                #Container for anime_tags
                anime_tags = container.find('div', class_="genres-inner").find_all('a')

                #Write into SQL database, table: animes
                for tag in anime_tags:
                    tag_id = tag.attrs['href'].replace('/anime/genre/', '').split('/')[0]
                    try:
                        run_inserts(DB,
                            insert_query2,(
                                int(anime_id), int(tag_id)
                            )
                        )
                    except Exception as e:
                        print('Failed to insert into anime_tags for anime_id: {0}, {1}'.format(anime_id, e))
                        pass

            #Provide stats for monitoring
            current_time = time.time()
            elapsed_time = current_time - start_time
            requests += 1    

            print('Requests Completed: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
            print('Elapased Time: {} minutes'.format(elapsed_time/60))
            print('Pausing...')    
            time.sleep(random.uniform(sleep_min, sleep_max))   

#Reviews scraper
def scrape_reviews(DB='anime.db', page_start=1, page_end=2350, sleep_min=9, sleep_max=18):    
    start_time = time.time()
    
    insert_query = '''
    INSERT OR IGNORE INTO reviews(
        review_id,
        anime_id, 
        username, 
        review_date,
        episodes_seen,
        overall_rating,
        story_rating,
        animation_rating,
        sound_rating,
        character_rating,
        enjoyment_rating,
        helpful_counts,    
        review_body
        ) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    for j in range(page_start, (page_end + 1)):

        #Makes the request
        url = 'https://myanimelist.net/reviews.php?t=anime&p={}'.format(j)
        headers = {
            "User-Agent": "mal review scraper for research."
        }
        print('Scraping: {}'.format(url))


        #Handle timeouts
        try:
            response = get(url, headers=headers, timeout = 10)
        except:
            print('Request timeout')
            pass

        if response.status_code != 200:
            print('Request: {}; Status code: {}'.format(requests, response.status_code))
            pass

        #Creates the soup object    
        html_soup = BeautifulSoup(response.text, 'html.parser')
        review_containers = html_soup.find_all('div', class_ = 'borderDark')

        #Loops through the containers on a page
        for container in review_containers:
            review_element = container.div

            #Review Id (Primary Key)
            review_id = container.find_all(
                'div', attrs={'style':"float: left; display: none; margin: 0 10px 10px 0"})[0].attrs['id'].replace('score', '')

            #Anime Id (Foreign Key)
            anime_id = review_element.find('a', class_='hoverinfo_trigger').attrs['rel'][0].replace('#revInfo', '')

            #Review info
            anime_name = (review_element.find('a', class_='hoverinfo_trigger').text)         
            username = (review_element.find_all('td')[1].a.text)
            review_date = (review_element.div.div.text)
            episodes_seen = (review_element.div.find_all('div')[1].text.strip().split(' ')[0])
            episodes_total = (review_element.div.find_all('div')[1].text.strip().split(' ')[2])

            #Review ratings
            overall_rating = (review_element.div.find_all('div')[2].text.strip().split('\n')[1])
            story_rating = (container.find_all('td', class_='borderClass')[3].text)
            animation_rating = (container.find_all('td', class_='borderClass')[5].text)
            sound_rating = (container.find_all('td', class_='borderClass')[7].text)
            character_rating = (container.find_all('td', class_='borderClass')[9].text)       
            enjoyment_rating = (container.find_all('td', class_='borderClass')[11].text)

            #Review helpful counts
            helpful_counts = (review_element.find('span').text)

            #Review Body
            body1 = container.select('div.spaceit.textReadability.word-break.pt8')[0].contents[4].strip()
            body2 = container.select('div.spaceit.textReadability.word-break.pt8')[0].contents[5].text.strip()
            review_body = (body1 + ' ' + body2).replace('\n', ' ').replace('\r', ' ')

            #Write into SQL database
            try:
                run_inserts(DB, insert_query,(
                    int(review_id), int(anime_id), username, review_date, \
                    episodes_seen, int(overall_rating), \
                    int(story_rating), int(animation_rating), int(sound_rating), \
                    int(character_rating), int(enjoyment_rating), int(helpful_counts), review_body)
                )
            except Exception as e:
                print('Failed to scrape anime_id: {0}, {1}'.format(anime_id, e))
                pass

        #Provide stats for monitoring
        current_time = time.time()
        elapsed_time = current_time - start_time
        requests = j + 1 - page_start    

        print('Requests Completed: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
        print('Elapased Time: {} minutes'.format(elapsed_time/60))
        if requests == page_end - page_start + 1:
            print('Scrape Complete')
            break
        print('Pausing...')    
        time.sleep(random.uniform(sleep_min, sleep_max))   

def scrape_all():
    scrape_studios(DB) 
    scrape_tags(DB)
    print('Pausing...')
    time.sleep(random.uniform(sleep_min, sleep_max))
    os.system('cls' if os.name == 'nt' else 'clear')
    print('Scraping anime data')
    scrape_animes(DB, sleep_min, sleep_max)
    print('Scraping review data')
    scrape_reviews(DB, page_start, page_end, sleep_min, sleep_max)
	
if __name__ == '__main__':
    scrape_all()