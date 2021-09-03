import re
from bs4 import BeautifulSoup
import requests 
import time
import numpy as np
import pandas as pd 
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 

headers = {'Accept-Language': 'en-US, en;q=0.5'}

url = 'https://www.imdb.com/chart/tvmeter/?ref_=nv_tvv_mptv'
response = requests.get(url, headers=headers).text

# Parse the content of the request with BeautifulSoup
page_html = BeautifulSoup(response, 'lxml')

# Select all the 50 movie containers from a single page
ts_containers = page_html.findAll('div', class_ = 'lister')

container = ts_containers[0]

# For every movie of these 100
# Scrape the title

title_s = [title.text for title in container.find_all('td', class_ = 'titleColumn')]
final_title = [title.replace('\n','').split('(')[0] for title in title_s]

# Scrape the year 
year_s= [year.text for year in container.find_all('span', class_ = 'secondaryInfo')]
final_year = [year.replace('(','').replace(')','') for year in year_s if re.match('\((\d{4})\)$',year)]

# Scrape the rating
rating_s = [rating.text if len(rating)>1 else 'NaN' for rating in container.findAll('td', {'class':'ratingColumn imdbRating'})]
final_rating = [rating.replace('\n','') for rating in rating_s]

# Scrape the number of votes
votes_s = [votes['title'] for votes in container.find_all('strong', title=True)]
final_votes = [votes.replace('user ratings','').split('on')[1].strip() for votes in votes_s]

'''Extract description for each tv-show'''

#options to remove chrome errors
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])

#read path
PATH = 'C:\Program Files (x86)\chromedriver.exe'
driver = webdriver.Chrome(executable_path=PATH,options=options)

#connect to the website
driver.get(url)

data_list = []
try:
    for i in final_title:
        link = driver.find_element_by_link_text(i)
        link.click()

        ts_desc = WebDriverWait(driver,5).until(
                EC.presence_of_all_elements_located(((By.XPATH, '//p[@class="GenresAndPlot__Plot-cum89p-6 bUyrda"]'))))
 
        for desc in ts_desc:
            data_list.append(desc.text)

        driver.back()

finally:
    driver.quit()

#Create a dataframe
ts_ratings = pd.DataFrame({'tvshow': final_title,
                              'year': final_year,
                              'rating': final_rating,
                              'description': data_list})

# Remove rows with NaN
ts_ratings = ts_ratings[~ts_ratings['rating'].isin(['NaN'])]
ts_ratings['votes'] = final_votes

# Change dtype
ts_ratings['year'] = pd.to_numeric(ts_ratings['year'])
ts_ratings['rating'] = ts_ratings['rating'].astype(float)
ts_ratings['votes'] = [float(str(i).replace(",", "")) for i in ts_ratings["votes"]]              

#ts_ratings.to_csv('tv_shows.csv')