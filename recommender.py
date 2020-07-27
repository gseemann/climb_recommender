import streamlit as st
from PIL import Image
import models
import pandas as pd 


default_range =15

#sidebars
# st.sidebar.header('Info')
# st.sidebar.text('subsection')

#test/title
st.title("Climb Recommender")

# img = Image.open('figures/8561A9D4-5B9B-4973-A54E-22BC5544AD6F_1_105_c.jpeg')
# st.image(img, caption='El Cajon Mountain, San Diego')

#header
st.header('Input the reference climb using Mountain Project ID')
st.subheader('You can include search area(using zip or city & state) and radius range in miles, \n https://www.mountainproject.com/area/classics <- link to climbs')

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
# pd.set_option('max_colwidth', 100)

#run recommender
if test:
	if climb_id:
		#spinner
		#below lines show we are done
		if len(climb_id)>10:
			climb_id = climb_id.split('/')[-2]
		#else we have climb id lets look it up
		st.success('Searching for similar climbs in that area')
		#call function and pass id, city, state, zip and radius
		#fxn returns df of 10 most similar climbs in search range
		st.dataframe(models.get_wrecked(target_id=climb_id, target_state=state,target_city=city,
			target_zipcode=zip_code,target_radius_range=radius_range,star_limit=3.5))
		st.success('Finished')
		st.balloons()
		#RUN recommender
	else:
		st.error('Please enter a valid ID/url into the climb id box')
		#ERROR please input a target climb


# img2 = Image.open('figures/09A21D41-981D-4FC1-A359-74653420A488_1_105_c.jpeg')
# st.image(img2, caption='View of the Witch in the Needles, CA')























