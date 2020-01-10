#!/usr/bin/env python
# coding: utf-8

# In[25]:


import config
import json
import requests
api_key = config.api_key
import time 
import datetime
import mysql.connector
from mysql.connector import errorcode
import pandas as pd



# In[26]:

#creates connection, all functions will start by calling this
def connect():
    global cnx
    cnx = mysql.connector.connect(
    host = config.host,
    user = config.user,
    passwd = config.password,
    database = 'climbs')
    global cursor
    cursor = cnx.cursor()


# In[9]:
#two functions used to create a new db

#sub_table function
def sub_db_create(cursor, database):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(database))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)


def create_db(db_name):
    global cnx
    cnx = mysql.connector.connect(
    host = config.host,
    user = config.user,
    passwd = config.password)
    global cursor
    cursor = cnx.cursor()
    try:
        cursor.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            sub_db_create(cursor, db_name)
            print("Database {} created successfully.".format(db_name))
            cnx.database = db_name
        else:
            print(err)
            exit(1)
    cursor.close()
    cnx.close()



#pass in a SELECT * FROM colleges and it returns results in a pandas dataframe
def query(query_string):
    connect()
    cursor = cnx.cursor()
    
    cursor.execute(query_string)
    results = cursor.fetchall()
    #close out db connection
    cursor.close()
    cnx.close()
    return results


#pass in a SELECT * FROM colleges and it returns results in a pandas dataframe
def query_to_df(query_string):
    connect()
    cursor = cnx.cursor()
    
    cursor.execute(query_string)
    
    df = pd.DataFrame(cursor.fetchall())
    df.columns = [x[0] for x in cursor.description]
    
    cursor.close()
    cnx.close()
    return df

#pass in a create table statement will, if table does not exist it will be created
def create_table(query):
    connect()
    
    try:
        print("Creating a new table")
        cursor.execute(query)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)
    else:
        print("OK")

    cursor.close()
    cnx.close()
    
#takes a list of tuples and adds them to the db    
def db_insert(tuple_list):
    connect()
    insert_statement = """INSERT IGNORE INTO routes(
                    id,
                    name,
                    type,
                    rating,
                    stars,
                    starVotes,
                    pitches,
                    location,
                    url,
                    longitude,
                    latitude)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    cursor.executemany(insert_statement, tuple_list)
    cnx.commit()
    cursor.close()
    cnx.close()
    
#takes list_of_dict and converts each dict from list to a tuple then inserts into the db
def route_to_tup(list_of_dict):
    list_of_tuples = []
    for i in list_of_dict:
        temp_tuple = ()
        temp_tuple = (i['id'],
              i['name'],
              i['type'],
              i['rating'],
              i['stars'],
              i['starVotes'],
              i['pitches'],
              ','.join(i['location']),    #converts list to str so we can input to sql
              i['url'],
              i['longitude'],
              i['latitude'])
        list_of_tuples.append(temp_tuple)
    db_insert(list_of_tuples)

    
    
def route_info_to_db(info):
    connect()
    insert_statement = """INSERT IGNORE INTO route_description(
                    id,
                    info)
                    VALUES (%s,%s)"""

    cursor.execute(insert_statement, info)
    cnx.commit()
    cursor.close()
    cnx.close()
