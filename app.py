# This Python file uses the following encoding: utf-8
#####################################################
#          ___                 _             _
#         /   |               (_)           (_)
#  _ __  / /| |_ __ ___   __ _ _ _ __  _   _ _
# | '_ \/ /_| | '_ ` _ \ / _` | | '_ \| | | | |
# | |_) \___  | | | | | | (_| | | | | | |_| | |
# | .__/    |_/_| |_| |_|\__,_|_|_| |_|\__,_|_|
# | |
# |_|
#####################################################
# Title:    p4mainui
# Version:  4.2
# Author:   Jonas Werner
#####################################################
import os
import json
from flask import Flask, render_template, redirect, request, url_for, make_response
import hashlib
import requests
import datetime
import random
from pyscbwrapper import SCB
from pymongo import MongoClient
import pymongo

# Set PWS environment if on Pivotal
if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = json.loads(os.environ['VCAP_SERVICES'])
    MONCRED = VCAP_SERVICES["mlab"][0]["credentials"]
    client = MongoClient(MONCRED["uri"])
    DB_NAME = str(MONCRED["uri"].split("/")[-1])

else:
    client = MongoClient('127.0.0.1:27017')
    DB_NAME = "p4mainui"

# Marvel keys
marvel_pub_key = os.environ['marvel_pub_key']
marvel_priv_key = os.environ['marvel_priv_key']

# Connect to MongoDB
db = client[DB_NAME]
# Clear out stale data
db.pageHits.drop()
# Add entries for each page
db.pageHits.insert_one({"page" : "apiSCB", "hitCount" : 0})
db.pageHits.insert_one({"page" : "apiChuckNorris", "hitCount" : 0})
db.pageHits.insert_one({"page" : "apiFelines", "hitCount" : 0})
db.pageHits.insert_one({"page" : "apiNasa", "hitCount" : 0})
db.pageHits.insert_one({"page" : "apiMath", "hitCount" : 0})
db.pageHits.insert_one({"page" : "apiMarvel", "hitCount" : 0})
db.pageHits.insert_one({"page" : "root", "hitCount" : 0})



app = Flask(__name__)
# my_uuid = str(uuid.uuid1())
offset = random.randint(0,500)
timestamp   = datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S')



def getScbData():

    # Open requests session to SCB database
    session = requests.Session()

    query = {
    "query": [
        {
        "code": "Region",
        "selection": {
            "filter": "vs:RegionLän99EjAggr",
            "values": [
            "18"
            ]
        }
        },
        {
        "code": "ContentsCode",
        "selection": {
            "filter": "item",
            "values": [
            "BE0101U1"
            ]
        }
        },
        {
        "code": "Tid",
        "selection": {
            "filter": "item",
            "values": [
            "2009",
            "2010",
            "2011",
            "2012",
            "2013",
            "2014",
            "2015",
            "2016",
            "2017",
            "2018"
            ]
        }
        }
    ],
    "response": {
        "format": "json"
    }
    }

    url = "http://api.scb.se/OV0104/v1/doris/en/ssd/START/BE/BE0101/BE0101C/BefArealTathetKon"
    # url = "http://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101C/BefArealTathetKon"

    response = session.post(url, json=query)
    response_json = json.loads(response.content.decode('utf-8-sig'))

    return response_json



def hash_params():
    """ Marvel API requires server side API calls to include
    md5 hash of timestamp + public key + private key """

    hash_md5 = hashlib.md5()
    hash_md5.update(f'{timestamp}{marvel_priv_key}{marvel_pub_key}'.encode('utf-8'))
    hashed_params = hash_md5.hexdigest()

    return hashed_params


@app.route('/')
def index():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'root'}, {'$inc': {'hitCount': 1}})

    content = make_response(render_template('dashBody02.html'))
    return content


@app.route('/localStats')
def localStats():

    hitCountPages = []
    hitCountValues = []
    # Display page hits stored in MongoDB
    cursor = db.pageHits.find()
    for page in cursor:
        hitCountPages.append(page['page'])
        hitCountValues.append(page['hitCount'])

    # Attempt to strip out ' marks in the data
    hitCountPages = [ i.strip("'") for i in hitCountPages ]
    hitCountValues = [ int(i) for i in hitCountValues ]

    content = make_response(render_template('dashPageStats.html', \
                        hitCountPages=hitCountPages, \
                        hitCountValues=hitCountValues \
                        ))
    return content


@app.route('/apiSCB')
def apiSCB():

    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiSCB'}, {'$inc': {'hitCount': 1}})

    graphLables = []
    graphData = []

    scbData = getScbData()

    for item in scbData['data']:
        graphLables.append(item['key'][1])
        graphData.append(item['values'][0])

    title1      = scbData['columns'][2]['text']
    graphLables = [ int(i) for i in graphLables ]
    graphData   = [ float(i) for i in graphData ]


    content = make_response(render_template('dashChart.html', \
                        bodyText1=title1, \
                        title1="Statistics for Örebro county in Sweden.", \
                        graphLables=graphLables, \
                        graphData=graphData \
                        ))

    return content



@app.route('/apiChuckNorris')
def apiChuckNorris():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiChuckNorris'}, {'$inc': {'hitCount': 1}})


    res = requests.get('https://api.chucknorris.io/jokes/random')
    results = res.json()

    chuckJoke   = results['value']
    chuckPic    = results['icon_url']
    # chuckDate   = results['updated_at']


    content = make_response(render_template('dashBasic.html', \
                        title1="Chuck Norris jokes", \
                        bodyText1="Example of using the Chuck Norris jokes DB API to pull random jokes", \
                        title2="Todays joke", \
                        bodyText2=chuckJoke, \
                        image1=chuckPic
                        ))

    return content


@app.route('/apiFelines')
def apiFelines():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiFelines'}, {'$inc': {'hitCount': 1}})

    url = 'https://cat-fact.herokuapp.com/facts/'
    res = requests.get(url)
    results = res.json()

    aaa = results['all']
    print("aaa: %s" % aaa)

    catFacts = []
    for entry in aaa:
        catFacts.append(entry['text'])

    content = make_response(render_template('dashCats.html', \
                        title1="Cat Facts", \
                        bodyText1="Way too many facts about cats", \
                        results=catFacts, \
                        ))

    return content


@app.route('/apiStarWars')
def apiStarWars():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiStarWars'}, {'$inc': {'hitCount': 1}})

    shipNumber = random.randint(9,17)
    url = 'https://swapi.co/api/starships/%s/' % shipNumber
    print("url: %s" % url)
    res = requests.get(url)
    results = res.json()

    content = make_response(render_template('dashTable.html', \
                        title1="Star Wars ship information", \
                        bodyText1="Example of using the Star Wars API to pull information on random ships", \
                        results=results, \
                        ))

    return content

@app.route('/apiNasa')
def apiNasa():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiNasa'}, {'$inc': {'hitCount': 1}})


    url = 'https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY'
    res = requests.get(url)
    results = res.json()

    title = results['title']
    date = results['date']
    explanation = results['explanation']
    imageUrl = results['url']

    content = make_response(render_template('dashBasic.html', \
                        title1=title, \
                        bodyText1="New pic from the NASA archives updated daily.", \
                        title2=date, \
                        bodyText2=explanation, \
                        image1=imageUrl, \
                        ))

    return content


@app.route('/apiMath')
def apiMath():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiMath'}, {'$inc': {'hitCount': 1}})

    url = 'http://numbersapi.com/random/trivia/'
    res = requests.get(url)
    results = res.content

    results = results.decode()

    content = make_response(render_template('dashBasic2.html', \
                        title1="Random Math trivia", \
                        bodyText1="Super-valuable information on the topic of math!", \
                        title2="Random trivia", \
                        bodyText2=results, \
                        ))

    return content

@app.route('/apiMarvel')
def apiMarvel():
    # Increase page hitcount in MongoDB
    db.pageHits.update({'page': 'apiMarvel'}, {'$inc': {'hitCount': 1}})

    # Gather required parameters for Marvel API call
    params = {'limit': 1, 'offset': offset, 'ts': timestamp, 'apikey': marvel_pub_key, 'hash': hash_params()};
    res = requests.get('https://gateway.marvel.com:443/v1/public/characters',
                    params=params)

    results = res.json()
    marvelCharacterName     = results['data']['results'][0]['name']
    marvelCharacterDesc     = results['data']['results'][0]['description']
    marvelCharacterPic      = results['data']['results'][0]['thumbnail']['path']
    marvelCharacterPicExt   = results['data']['results'][0]['thumbnail']['extension']
    marvelCharacterPicture  = marvelCharacterPic + "/portrait_xlarge." + marvelCharacterPicExt


    content = make_response(render_template('dashBasic.html', \
                        title1="Marvel information", \
                        bodyText1="Example of using Marvels API to pull random character information", \
                        title2=marvelCharacterName, \
                        bodyText2="Character info: " + marvelCharacterDesc, \
                        image1=marvelCharacterPicture
                        ))

    return content



if __name__ == "__main__":
	app.run(    debug=False, \
                host='0.0.0.0', \
                port=int(os.getenv('PORT', '5000')), threaded=True)
