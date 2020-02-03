#import libraries
import pandas as pd

#for api calls
from bs4 import BeautifulSoup
import requests
import json


#personal api and aws keys
import config

import query_helper


#helper functions

def get_route_info(id_):
    
    #get page content
    web_address = f'https://www.mountainproject.com/route/{id_}'
    
    page = requests.get(web_address)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    #grab section of interest
    info =soup.find_all(class_='fr-view')
    
    describe=[]
    for i in range(len(info)):
        describe.append(info[i].get_text())
    
    return describe

def get_route_details(route_id):
    url_params = {  'routeIds': str(route_id),
                    'key': config.api_key
                 }
    #call API and get basic route info
    url = 'https://www.mountainproject.com/data/get-routes'
    response = requests.get(url, params=url_params)

    # cast data to json format
    data = response.json()

    #check that call successful 
    if data['success']:
        routes = data['routes']
        #store route data in mysql
        query_helper.route_to_tup(routes)
    #print error message if something goes wrong
    else:
        f'Error!! '
        
    #scrape route description
    description = get_route_info(route_id)
    #store in db
    query_helper.route_info_to_db((route_id, '-'.join(description)))
    
    #now clean the data
    #load in our new route to begin cleaning
    df = query_helper.query_to_df(f'SELECT * FROM routes WHERE id={route_id}')

    #add sub location columns
    df['location']=df['location'].apply(lambda x: x.split(','))

    #store location and add in new areas and sub areas
    query_helper.route_info_to_db((route_id, '-'.join(description)))
    #new sub areas 
    df['region'] =0
    df['area']=0
    df['sub_area']=0
    df['wall']=0

    #determines length of sub location list and splits them into appropriate columns
    def split_list(array, length):
        if length ==5:
            if len(array)>=5:
                return ','.join(array[4:])
            else:
                return 0
        if len(array)>= length:
            return array[length-1]
        else:
            return 0

    #parse area info (note size varies and we only split into 5 sections)
    df.region =df.location.apply(lambda x: split_list(x,2))
    df.area =df.location.apply(lambda x: split_list(x,3))
    df.sub_area =df.location.apply(lambda x:  split_list(x,4))
    df.wall =df.location.apply(lambda x:  split_list(x,5))

    #then make location state only
    df.location = df.location.apply(lambda x: x[0])  

    #fill in blank types as trad (theres only a few)
    df.type = df.type.apply(lambda x: 'Trad' if x=='' else x)

    #add columns to breakout climbing types
    df['Sport'] =0
    df['Trad']=0
    df['Boulder']=0
    df['TR']=0
    df['Alpine'] =0
    df['Aid']=0
    df['Ice']=0
    df['Snow'] =0
    df['Mixed']=0

    df['Sport'] =df['type'].apply(lambda x: 1 if 'Sport' in x else 0)
    df['Trad']=df['type'].apply(lambda x: 1 if 'Trad' in x else 0)
    df['Boulder']=df['type'].apply(lambda x: 1 if 'Boulder' in x else 0)
    df['TR']=df['type'].apply(lambda x: 1 if 'TR' in x else 0)
    df['Alpine'] =df['type'].apply(lambda x: 1 if 'Alpine' in x else 0)
    df['Aid']=df['type'].apply(lambda x: 1 if 'Aid' in x else 0)
    df['Ice']=df['type'].apply(lambda x: 1 if 'Ice' in x else 0)
    df['Snow'] =df['type'].apply(lambda x: 1 if 'Snow' in x else 0)
    df['Mixed']=df['type'].apply(lambda x: 1 if 'Mixed' in x else 0)

    #drop this col as we now have that data distributed across other columns
    df.drop(columns='type',inplace=True)

    def pitches_wo_boulders(row):
        if (row['pitches']==0)&(row['Boulder']==0):
            return 1
        else:
            return row['pitches']

    #change all non boulders with zero to 1 pitch
    df.pitches =df.apply(pitches_wo_boulders, axis=1)

    # change negative pitch counts to 1
    df.pitches =df.pitches.apply(lambda x: 1 if x<0 else x)

    #clean diff rating
    #start by making dict of grades/ratings
    diff_grade = {'Rope': ['3rd',
      '4th',
      'Easy 5th',
      '5.0',
      '5.1',
      '5.2',
      '5.3',
      '5.4',
      '5.5',
      '5.6',
      '5.7',
      '5.7+',
      '5.8-',
      '5.8',
      '5.8+',
      '5.9-',
      '5.9',
      '5.9+',
      '5.10a',
      '5.10-',
      '5.10a/b',
      '5.10b',
      '5.10',
      '5.10b/c',
      '5.10c',
      '5.10+',
      '5.10c/d',
      '5.10d',
      '5.11a',
      '5.11-',
      '5.11a/b',
      '5.11b',
      '5.11',
      '5.11b/c',
      '5.11c',
      '5.11+',
      '5.11c/d',
      '5.11d',
      '5.12a',
      '5.12-',
      '5.12a/b',
      '5.12b',
      '5.12',
      '5.12b/c',
      '5.12c',
      '5.12+',
      '5.12c/d',
      '5.12d',
      '5.13a',
      '5.13-',
      '5.13a/b',
      '5.13b',
      '5.13',
      '5.13b/c',
      '5.13c',
      '5.13+',
      '5.13c/d',
      '5.13d',
      '5.14a',
      '5.14-',
      '5.14a/b',
      '5.14b',
      '5.14',
      '5.14b/c',
      '5.14c',
      '5.14+',
      '5.14c/d',
      '5.14d',
      '5.15a',
      '5.15-',
      '5.15a/b',
      '5.15b',
      '5.15',
      '5.15c',
      '5.15+',
      '5.15c/d',
      '5.15d'],
     'Boulder': ['V-easy',
      'V0-',
      'V0',
      'V0+',
      'V0-1',
      'V1-',
      'V1',
      'V1+',
      'V1-2',
      'V2-',
      'V2',
      'V2+',
      'V2-3',
      'V3-',
      'V3',
      'V3+',
      'V3-4',
      'V4-',
      'V4',
      'V4+',
      'V4-5',
      'V5-',
      'V5',
      'V5+',
      'V5-6',
      'V6-',
      'V6',
      'V6+',
      'V6-7',
      'V7-',
      'V7',
      'V7+',
      'V7-8',
      'V8-',
      'V8',
      'V8+',
      'V8-9',
      'V9-',
      'V9',
      'V9+',
      'V9-10',
      'V10-',
      'V10',
      'V10+',
      'V10-11',
      'V11-',
      'V11',
      'V11+',
      'V11-12',
      'V12-',
      'V12',
      'V12+',
      'V12-13',
      'V13-',
      'V13',
      'V13+',
      'V13-14',
      'V14-',
      'V14',
      'V14+',
      'V14-15',
      'V15-',
      'V15',
      'V15+',
      'V15-16',
      'V16-',
      'V16',
      'V16+',
      'V16-17',
      'V17-',
      'V17'],
     'Ice': ['WI1',
      'WI2-',
      'WI2',
      'WI2+',
      'WI2-3',
      'WI3-',
      'WI3',
      'WI3+',
      'WI3-4',
      'WI4-',
      'WI4',
      'WI4+',
      'WI4-5',
      'WI5-',
      'WI5',
      'WI5+',
      'WI5-6',
      'WI6-',
      'WI6',
      'WI6+',
      'WI6-7',
      'WI7-',
      'WI7',
      'WI7+',
      'WI7-8',
      'WI8-',
      'WI8',
      'AI1',
      'AI1-2',
      'AI2',
      'AI2-3',
      'AI3',
      'AI3-4',
      'AI4',
      'AI4-5',
      'AI5',
      'AI5-6',
      'AI6'],
     'Aid': ['C0',
      'A0',
      'C0+',
      'A0+',
      'C0-1',
      'A0-1',
      'C1-',
      'A1-',
      'C1',
      'A1',
      'C1+',
      'A1+',
      'C1-2',
      'A1-2',
      'C2-',
      'A2-',
      'C2',
      'A2',
      'C2+',
      'A2+',
      'C2-3',
      'A2-3',
      'C3-',
      'A3-',
      'C3',
      'A3',
      'C3+',
      'A3+',
      'C3-4',
      'A3-4',
      'C4-',
      'A4-',
      'C4',
      'A4',
      'C4+',
      'A4+',
      'C4-5',
      'A4-5',
      'C5-',
      'A5-',
      'C5',
      'A5',
      'C5+',
      'A5+'],
     'Mixed': ['M1',
      'M1+',
      'M1-2',
      'M2-',
      'M2',
      'M2+',
      'M2-3',
      'M3-',
      'M3',
      'M3+',
      'M3-4',
      'M4-',
      'M4',
      'M4+',
      'M4-5',
      'M5-',
      'M5',
      'M5+',
      'M5-6',
      'M6-',
      'M6',
      'M6+',
      'M6-7',
      'M7-',
      'M7',
      'M7+',
      'M7-8',
      'M8-',
      'M8',
      'M8+',
      'M8-9',
      'M9-',
      'M9',
      'M9+',
      'M9-10',
      'M10-',
      'M10',
      'M10+',
      'M10-11',
      'M11-',
      'M11',
      'M11+',
      'M12-',
      'M12',
      'M12+',
      'M13-',
      'M13',
      'M13+'],
     'Snow': ['Easy Snow', 'Mod. Snow', 'Steep Snow'],
     'Safety': [
     'PG13',
      'R',
      'X'],
     'Mountaineering': ['I', 'II', 'III', 'IV', 'V', 'VI']}

    #parses our difficulty rating and specified substring
    #returns grade if boulder or rope passed as catagory
    def get_grade_sub(string, catagory):
        words = string.split()
        for word in words:
            if word in diff_grade[catagory]:
                return word

        #else we couldn't find the danger grade so return 0 
        if catagory == "Safety":
            return "G"
        #else we couldn't find the difficulty grade so return 0(note this is different from above G rating)
        if (catagory == 'Rope') | (catagory == 'Boulder'):
            return 0

    #adding danger rope and boulder columns
    df['danger'] = 'G'
    df['rope_grade'] = 0
    df['boulder_grade'] = 0
    df['danger'] = df['rating'].apply(lambda x: get_grade_sub(x, 'Safety'))
    df['rope_grade'] = df['rating'].apply(lambda x: get_grade_sub(x, 'Rope'))
    df['boulder_grade'] = df['rating'].apply(lambda x: get_grade_sub(x, 'Boulder'))

    ### make ordinal columns for rope_grade, boulder_grade and danger
    def get_rope_grades(grade, catagory):
        for i,match in enumerate(diff_grade[catagory]):
            if match == str(grade):
                return i+1
        return 0    

    #clean routes missing grade
    df['rating'] =df['rating'].apply(lambda x: '_' if x=='' else x)
    #make grades and danger numeric
    df['rope_grade']=df['rating'].apply(lambda x: get_rope_grades(x.split()[0],'Rope'))
    df['boulder_grade']=df['rating'].apply(lambda x: get_rope_grades(x.split()[0],'Boulder'))
    df['danger']=df['rating'].apply(lambda x: get_rope_grades(x.split()[-1],'Safety'))

    ##add on description
    df['infos']='-'.join(description)

    #new keyword columns
    key_words = ['slab', 'traverse', 'roof', 'corner', 'crack', 'face','flake', 'finger', 'fingers',
                 'hand', 'hands', 'arch', 'balancy', 'balance', 'jug', 'squeeze', 'mantel', 'sustained',  
                 'ramp', 'overhung', 'dihedral', 'sporty', 'heady', 'pump', 'pumpy', 'technical',
                 'run out', 'mental', 'well protected', 'chimney', 'offwidth', 'stem', 'arete', 'exposed', 'exposure',
                 'crimp','crimpy', 'vertical', 'slabby', 'cave', 'steep', 'bouldery', 'powerful','runout','run-out']
    #the above key words will be mapped to the below subset of words
    col_key_words = ['slab', 'traverse', 'roof', 'corner', 'crack', 'hand', 'face','flake', 'fingers',
                     'jug', 'exposed', 'dihedral', 'sustained', 'technical','run out', 'well protected',
                     'chimney', 'offwidth', 'stem', 'arete','crimp', 'vertical', 'powerful']
    sym_map = {
     'finger':'fingers',
     'hands':'hand',
     'arch': 'roof',
     'balancy':'technical',
     'heady':'run out',
     'runout':'run out',
     'run-out':'run out',
     'pumpy':'sustained',
     'exposure':'exposed',
     'crimpy':'crimp',
     'slabby':'slab',
     'bouldery':'powerful',
     'cave':'roof',
     'overhung':'roof',
     'squeeze':'chimney',
     'steep':'vertical',
     'balance':'technical',
     'mental':'run out',
     'ramp':'slab',
     'mantel':'technical',
     'sporty':'well protected',
     'pump':'sustained',
     'jam':'crack'
    }
    #making columns
    for adj in col_key_words:
        df[adj]=0
    df.head()

    #count if key word in description
    for word in col_key_words:
        df[word] = df['infos'].apply(lambda x: 1 if word in str(x) else 0)
    #take care to account for synonyms
    for k,v in sym_map.items():
        df[v] = df['infos'].apply(lambda x: 1 if k in str(x) else 0)   

    #write to csv and well add to our main df in a moment
    df.to_csv('data/target_climb.csv')
    
    #success
    return 1
