###########version used on heroku############
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
from sklearn import preprocessing
from math import sin, cos, sqrt, atan2, radians

import json

#for rec model
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import polynomial_kernel
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.metrics.pairwise import laplacian_kernel
from sklearn.metrics.pairwise import chi2_kernel
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import minmax_scale
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import StandardScaler

# function is passed climb id and search params and return top 10 recommended climbs
def get_wrecked(target_id, target_state=None,target_city=None,target_zipcode=None,target_radius_range= 60,star_limit=3.5):


    df_numeric = pd.read_csv('data/df.csv', index_col='id')
    #reorder columns
    df_numeric =df_numeric[['name', 'rating', 'stars', 'starVotes', 'pitches', 'location', 'region',
                                   'area', 'sub_area', 'wall', 'longitude', 'latitude', 'url', 'Sport',
                                   'Trad', 'Boulder', 'TR', 'Alpine', 'Aid', 'Ice', 'Snow', 'Mixed',
                                   'danger', 'rope_grade', 'boulder_grade', 'infos', 'slab', 'traverse',
                                   'roof', 'corner', 'crack', 'hand', 'face', 'flake', 'fingers', 'jug', 'exposed',
                                   'dihedral', 'sustained', 'technical', 'run out', 'well protected',
                                   'chimney', 'offwidth', 'stem', 'arete', 'crimp', 'vertical', 'powerful',
                                   'in_range']]

    target_id = int(target_id)
    # # target_lat = 32.9127 
    # # target_lon = -116.882
    # target_state =''
    # target_city =''
    # target_zipcode = '92008'
    #only cast if string passed in

    target_radius_range = int(target_radius_range)

    star_limit = int(star_limit)


    # ### Get coordinates for zip or city
    with open('data/us-zip-code-latitude-and-longitude.json') as f:
      coord_dict = json.load(f)


    # In[5]:


    def get_coords(target_city=None, target_state=None, zipcode=None):
        #find the coordinates for city or zip code
        for city in coord_dict:
            if city['fields']['zip']==zipcode:
                return city['fields']['latitude'],city['fields']['longitude']
            if (city['fields']['state']==target_state)&(city['fields']['city']==target_city):
                return city['fields']['latitude'],city['fields']['longitude']
        #if nothing is found return none
        return None, None


    # In[6]:


    target_lat, target_lon = get_coords(target_city, target_state, target_zipcode)


    # In[7]:


    print(target_lat, target_lon)


    ## Create fxn to see if climb is in search range
    #function takes search param range and assigns to original df if climb in_range
    def in_range(df_fxn, lat, lon, radius_range=None):
        if radius_range:
            R= 3958.8 
            if (lat == None)|(lon==None):
                df_fxn['in_range'] = 1
            else:
                #assign target coords and set to radians for calc
                lat1 = radians(lat)
                lon1 = radians(lon)
                for index, row in df_fxn.iterrows():
                    #assign the lat and lon for each climb
                    lat2 = radians(row['latitude'])
                    lon2 = radians(row['longitude'])

                    dlon = lon2 - lon1
                    dlat = lat2 - lat1

                    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1 - a))

                    distance = R * c

                    #assign in_range col to 1 if the climb is in range
                    if distance < radius_range:
                        df_fxn.at[index,'in_range']=1
                    else:
                        df_fxn.at[index,'in_range']=0   
        else:
            df_fxn['in_range'] =1


    def star_cutoff(df_fxn, star_limit=3.5):
        for index, row in df_fxn.iterrows():
            #assign in_range col to 1 if the climb is in range
            if (df_fxn.at[index, 'stars'] >= star_limit)&(df_fxn.at[index, 'in_range']!=0):
                df_fxn.at[index,'in_range']=1
            else:
                df_fxn.at[index,'in_range']=0   

    ## used to get list of climbs allowed for comparison
    in_range(df_numeric, lat = target_lat, lon = target_lon, radius_range=target_radius_range)


    # ### Star cutoff (ie only give results for routes with above 3.5 stars)
    star_cutoff(df_numeric, star_limit)

    # ### To begin, see if if the climb already exists in db
    if target_id in df_numeric.index:
        print('We have climb already')
        #make sure reference climb is assigned in_range
        df_numeric.loc[target_id,'in_range']=1
    else:   #climb is not in db and we tell user to select a different climb
        return pd.DataFrame(np.array(['You selected a climb outside database']),
                   columns=['ERROR'])
        


    #### Create df_in_range to run recommender in subset
    df_in_range = df_numeric[df_numeric['in_range']==1].reset_index()      
    target_index =df_in_range.index[df_in_range['id']==target_id][0] #store target climb index in subset that will be compared



    #creates features from df_in_range used for comparison
    features = df_in_range.loc[:,['stars', 'pitches', 'Sport', 'Trad', 'Boulder', 'TR', 'Alpine', 'Aid',
           'Ice', 'Snow', 'Mixed', 'danger', 'rope_grade', 'boulder_grade', 'slab', 'traverse', 'roof', 
                    'corner', 'crack', 'hand', 'face','flake', 'fingers',
                     'jug', 'exposed', 'dihedral', 'sustained', 'technical','run out', 'well protected',
                     'chimney', 'offwidth', 'stem', 'arete','crimp', 'vertical', 'powerful']] #,'longitude','latitude',



    min_max_scaler = MinMaxScaler()
    scalar = StandardScaler()
    ##### Pick a scaling option ###############################

    # features_scaled = scalar.fit_transform(features)
    # features_scaled = min_max_scaler.fit_transform(features.drop(columns=['danger','pitches']))

    features_scaled = min_max_scaler.fit_transform(features)

    # scale danger and pitches using ss and add into features scaled df
    # features_scaled = np.concatenate((features_scaled, scalar.fit_transform(features[['danger', 'pitches']])), axis=1)

    ##################################################################

    for i in range(features_scaled.shape[0]):
        features_scaled[i][10]=features_scaled[i][12]*10  #weight rope_grade higher
        features_scaled[i][11]=features_scaled[i][13]*10 #weight boulder_grade higher


    # ### Now lets fit the similarity model

    # #### Rec function

    # In[30]:


    def get_recommendations(idx, kernel_type):

        #value to store scores and indicies
        score_matrix = np.ndarray(shape=(len(df_in_range),2), dtype=float)

        #go through the target climb vs all onthers in our db and populate score mtx with index and similarity
        for i in range(df_in_range.shape[0]):
            score = kernel_type(features_scaled[idx].reshape(1,-1),features_scaled[i].reshape(1,-1))
            score_matrix[i][0] =  i        ##the index comparison corresponding to the score
            score_matrix[i][1] = score     ##the score for the current index

        # Sort the climbs based on the similarity scores
        score_matrix = sorted(score_matrix, key=lambda x: x[1], reverse=True)
        

    #########################  WIP ADD/calculate SIMilarity VALUE from tf-idf infos comparison #######################

        # # Get the scores of the 20 most similar climbs
        score_matrix = score_matrix[:11]

        # # Get the climb indices (& cast to ints)
        climb_indices = [int(i[0]) for i in score_matrix]
        
        # Return the top 20 most similar climbs
        return df_in_range.loc[climb_indices,:].reset_index()



    rec=get_recommendations(target_index, cosine_similarity)
    rec = rec[['name', 'rating', 'stars', 'starVotes', 'pitches', 'location', 'region',
                                   'area', 'sub_area', 'wall', 'longitude', 'latitude', 'url', 'Sport',
                                   'Trad', 'Boulder', 'TR', 'Alpine', 'Aid', 'Ice', 'Snow', 'Mixed',
                                   'danger', 'rope_grade', 'boulder_grade', 'infos', 'slab', 'traverse',
                                   'roof', 'corner', 'crack', 'hand', 'face', 'flake', 'fingers', 'jug', 'exposed',
                                   'dihedral', 'sustained', 'technical', 'run out', 'well protected',
                                   'chimney', 'offwidth', 'stem', 'arete', 'crimp', 'vertical', 'powerful']]
    return rec 
