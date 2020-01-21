import streamlit as st
from PIL import Image
import models
import pandas as pd 

default_range =60

#test/title
st.title("Climb Recommender")

img = Image.open('8561A9D4-5B9B-4973-A54E-22BC5544AD6F_1_105_c.jpeg')
st.image(img, caption='El Cajon Mountain, San Diego')

#header
st.header('Input the reference climb using Mountain Project ID')
st.subheader('You can include search area(using zip or city & state) and radius range in miles')

#ask user for input
climb_id = st.text_input('Enter target climb ID (or mountain project url for target climb):')

zip_code = st.text_input('Enter zip code to search for similar climbs in that area:', '92008')
st.info('Or search by city and state')
city = st.text_input('Enter city to search in that area:', '')
state = st.text_input('Enter state to search in that area:', '')

st.text('Lastly, enter the search radius (defaults to 60 miles)')
radius_range = st.number_input('Enter radius to search in specified area:', default_range)


#once button pressed we check for input errors and start search
test = st.button('Search for recommended climbs')

if test:
	if climb_id:
		st.success('Searching for similar climbs in that area')
		#call function and pass id, city, state, zip and radius
		#fxn returns df of 10 most similar climbs in search range
		st.dataframe(models.get_wrecked(target_id=climb_id, target_state=state,target_city=city,
			target_zipcode=zip_code,target_radius_range=radius_range,star_limit=3.5))

		#RUN recommender
	else:
		st.error('Please enter a valid ID/url into the climb id box')
		#ERROR please input a target climb


























