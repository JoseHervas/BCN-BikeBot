import json, requests, telebot, pandas
from math import cos, asin, sqrt

#Web api from the public Bicing service of Barcelona
url = 'http://wservice.viabicing.cat/v2/stations'

#Bot token
bot = telebot.TeleBot("API-KEY")

#Read and parse the data from the bicing service
def data_scratch(webpage):
	resp = requests.get(url=url)
	raw_data = json.loads(resp.text)
	stations = [{'id':station['id'],'streetName':station['streetName'], 'bikes':station['bikes'], 'status':station['status'], 'latitude':station['latitude'], 'longitude':station['longitude']} for station in raw_data['stations']]
	return stations

#Starting instructions	
@bot.message_handler(commands=['start'])
def send_welcome(message):
        chat_id = message.chat.id
        text = '''
        Hello! I'm the BCN BikeBot.
	\nI will help you to know how many bikes are available in your near Bicing stations.
	\nJust write "/nearstations" and send your location. I will search for stations close to you with more than 5 bikes available at the moment and I will send you their location.
        \nYou can also ask me about a particular Bicing station, or about a particular street (but note that this functionality is under development at this moment).
	\nType "/help" to know more tips about me.
	'''
        bot.send_message(chat_id, text)

#Help instructions
@bot.message_handler(commands=['help'])
def help(message):
        chat_id = message.chat.id
        text = '''
        Basic commands:\n
- /nearstations will allow you to find your closest station with more than 5 bikes available at the moment.
- /station + a station number will allow you to see how many bikes are available at that station.
- /street + a street name will allow you to see how many bikes are available on the stations from that street at the moment.
- /info will display a list with all the streets and stations.
- /fullinfo will display a list with all the streets, the stations, and the number of bikes available on each one at the moment.\n
If you want to report a bug or contact my creator, send a mail to jhervasdiaz@gmail.com
        '''
        bot.send_message(chat_id, text)

#/nearstations
@bot.message_handler(commands=['nearstations'])
def station_info(message):
    chat_id = message.chat.id
    text = "Ok. Send me your location now."
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    itembtn = telebot.types.KeyboardButton('Send my location.', request_location=True)
    markup.add(itembtn)
    bot.send_message(chat_id, text,reply_markup=markup)

#i'll use the haversine formula to calculate the distance between two points
def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))

#closest point from "data" to "v"
def closest(data, v):
    return data.index(min(data, key=lambda p: distance(v['latitude'],v['longitude'],p['latitude'],p['longitude'])))

#find the closest station to the user with status == OPN and bikes > 5
@bot.message_handler(content_types=['location'])
def find_near_stations(message):
    try:
        stations = data_scratch(url)
        stations_coordinates = [{'latitude':float(station['latitude']),'longitude':float(station['longitude'])} for station in stations if int(station['bikes']) > 5 and station['status'] == 'OPN']
        user_location = {'latitude':message.location.latitude, 'longitude':message.location.longitude}
        nearest_station = closest(stations_coordinates, user_location)
        print(stations_coordinates[nearest_station], distance(user_location['latitude'],user_location['longitude'],float(stations_coordinates[nearest_station]['latitude']),float(stations_coordinates[nearest_station]['longitude'])))
        chat_id = message.chat.id
        text = "I've found this station. It's the nearest station to you with more than 5 bikes at this moment."
        bot.send_message(chat_id, text)
        bot.send_location(chat_id, stations_coordinates[nearest_station]['latitude'],stations_coordinates[nearest_station]['longitude'])
    except:
        text = '''
        Ooooops! Something has crashed while I was trying to find your nearest station.\n
Please, try it again, and if the problem persists, contact jhervasdiaz@gmail.com
        '''
        bot.send_message(chat_id, text)

#search the indicated station. If it's open, returns the number of bikes available at the moment. If it's close, returns a close notification.    
@bot.message_handler(commands=['station'])
def station_info(message):
    chat_id = message.chat.id
    try:
        stations = data_scratch(url)
        station_id = message.text.split('/station ')[1]
        num_bikes = [station['bikes'] for station in stations if station['id'] == str(station_id)]
        status = [station['status'] for station in stations if station['id'] == str(station_id)]
        if (status[0] == 'OPN'):
            text = "The station nº " + str(station_id) + " has actually " + str(num_bikes[0]) + " bikes available at this moment."
        else:
            text = "The station nº " + str(station_id) + " is closed at this moment."
        bot.send_message(chat_id, text)
    except:
        text = '''
        Ooooops! Something has crashed while I was trying to find that station.\n
Please, try it again, and if the problem persists, contact jhervasdiaz@gmail.com
        '''
        bot.send_message(chat_id, text)

#search the station on the indicated street. If it's open, returns the number of bikes available at the moment. If it's close, returns a close notification.
#Actually this script only returns the first station located on this street, but one street on BCN can have more than one station,
#This bug needs to be fixed on next releases.
@bot.message_handler(commands=['street'])
def street_info(message):
    chat_id = message.chat.id
    try:
        stations = data_scratch(url)
        street_name = message.text.split('/street ')[1]
        num_bikes = [station['bikes'] for station in stations if station['streetName'] == str(street_name)]
        status = [station['status'] for station in stations if station['streetName'] == str(street_name)]
        if (status[0] == 'OPN'):
            text = "The station of the street " + str(street_name) + " has actually " + str(num_bikes[0]) + " bikes available at this moment."
        else:
            text = "The station of the street " + str(street_name) + " is closed at this moment."
        bot.send_message(chat_id, text)
    except:
        text = '''
        Ooooops! Something has crashed while I was trying to find that station.\n
Please, try it again, and if the problem persists, contact jhervasdiaz@gmail.com
        '''
        bot.send_message(chat_id, text)

#returns a pandas table with all the stations and the streets. The list is limited by the big number of stations that there are on BCN.
#this will be fixed on future releases.
@bot.message_handler(commands=['info'])
def info(message):
    chat_id = message.chat.id
    try:
        stations = data_scratch(url)
        table = pandas.DataFrame(stations)
        table = table[['id', 'streetName']]
        text = str(table)
        bot.send_message(chat_id, text)
    except:
        text = '''
        Ooooops! Something has crashed while I was trying to find the stations.\n
Please, try it again, and if the problem persists, contact jhervasdiaz@gmail.com
        '''
        bot.send_message(chat_id, text)

#returns a pandas table with all the stations, the streets and the number of available bikes on each one. The list is limited by the big number of stations that there are on BCN.
#this will be fixed on future releases.
@bot.message_handler(commands=['fullinfo'])
def fullinfo(message):
    chat_id = message.chat.id
    try:
        stations = data_scratch(url)
        table = pandas.DataFrame(stations)
        text = str(table)
        bot.send_message(chat_id, text)
    except:
        text = '''
        Ooooops! Something has crashed while I was trying to find the stations.\n
Please, try it again, and if the problem persists, contact jhervasdiaz@gmail.com
        '''
        bot.send_message(chat_id, text)

bot.polling()
