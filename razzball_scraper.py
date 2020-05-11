from bs4 import BeautifulSoup
import requests

def get_pitchers():
    page = requests.get("https://razzball.com/steamer-pitcher-projections/")
    soup = BeautifulSoup(page.content,'html.parser')
    print(soup)
    #tree = html.fromstring(page.content)
    #table_bod = tree.xpath('//table[@id="neorazzstatstable"]/@tbody/')
    #table_ros = []
    #print(tree.xpath('//table[@id="neorazzstatstable"]/@tbody/@tr/@td/text()'))

if __name__ == "__main__":
    get_pitchers()
