import json
import requests
from bs4 import BeautifulSoup



def get_mush_table(web_address):
    
    page = requests.get(web_address)
    soup = BeautifulSoup(page.content, 'html.parser')

    ### IF IMPORT IS MESSED UP LOOK HERE. ASSUMES mush Box is always second
    info = soup.find_all('table',{"class":"infobox"})

    #get mushroom name 
    name = [i.string for i in info[1].findAll('i')]

    #get mushroom info
    divs = info[1].findAll("td")
    stuff= divs[1:]
    text = []
    for i in stuff:
        text.append(i.get_text())

    name_and_info = name+text
    
    
    
    #catch if only name is missing
    if (len(text)==7):
        name = [web_address.split('/')[-1].replace('_', ' ')]
        name_and_info = name+text

    #catch incomplete values and return them seperate and add them to a list
    if(len(name_and_info)!=8):
        name = [web_address.split('/')[-1].replace('_', ' ')]
        name_and_info =name+text
        return name_and_info

    #store into dict and return
    mushroom_dict ={
        'name'          :name_and_info[0],
        'hymeniumType'  :name_and_info[1],
        'capShape'      :name_and_info[2],
        'whichGills'    :name_and_info[3],
        'stipeCharacter':name_and_info[4],
        'sporePrintColor':name_and_info[5],
        'ecologicalType':name_and_info[6],
        'howEdible'      :name_and_info[7]
    }
    
    mush_list=[]
    mush_list.append(mushroom_dict)
    
    return mush_list