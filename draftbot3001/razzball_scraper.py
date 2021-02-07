from bs4 import BeautifulSoup
import requests
import re
import csv


class Scraper:
    def get_pitchers(self):
        '''
        Downloads pitcher projections and projected auction draft prices for pitchers from razzball.com. 
        Projections are razzball/steamer projections
        '''
        download_table("https://razzball.com/steamer-pitcher-projections/", 'data/razzball-pitchers.csv')
        download_table("https://razzball.com/preseason-playerrater-pitchercategories/", 'data/razzball-pitchers-prices.csv')

    def get_hitters(self):
        '''
        Downloads hitter projections and projected auction draft prices for pitchers from razzball.com. 
        Projections are razzball/steamer projections
        '''
        download_table("https://razzball.com/steamer-hitter-projections/", 'data/razzball-hitters.csv')
        download_table("https://razzball.com/playerrater-preseason-hittercategories-espn/", 'data/razzball-hitters-prices.csv')

def download_table(link, outfl):
    '''
    Given a link and the name of a file, downloads the page at the link and outputs the table in csv format to the file specified by outfl. 
    To be used to obtain player data from razzball.com. 
    '''
    # First, download the webpage
    page = requests.get(link)
    soup = BeautifulSoup(page.content,'html.parser')

    # get the header 
    header = soup.find_all('thead')[0].find_all('th')

    # get the actual table
    results = soup.find_all('tbody')
    all_players = results[1].find_all('tr')
    count = 1

    # write the table to the csv file
    with open(outfl, mode='w', newline='') as razzball_data:
        writer = csv.writer(razzball_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # first write the header
        writer.writerow([i.text for i in header])

        # then for each player write their data to a new row
        for player in all_players:
            row = player.find_all('td')
            row_list = [i.text for i in row]
            row_list[0] = count
            writer.writerow(row_list)
            count += 1

if __name__ == "__main__":
    scraper = Scraper()
    scraper.get_pitchers()
    scraper.get_hitters()