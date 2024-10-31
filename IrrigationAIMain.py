# identify if critical right now, if not then ask how many days do you think that it has, and then depending on that then it goes to GPT. 

import requests
import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from ttkbootstrap import Style
from openai import OpenAI



api_key = 'OPENAI API KEY'
client = OpenAI(api_key = api_key)


def clear_widgets(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def correct():
    global timeList, temperatureHourlyList, timeList, windHourlyList, compositePrecpitationList, humidityHourlyList

    openaiRESPONSE = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
        "role": "system",
        "content": "You are an expert at crop irrigation and agriculture. After many years of experience in farming of all sorts of crops, you know how to find the optimal time for irrigation of a crop based on climate data that is given to you. Each list describes a different data point. Each element in a list represents information about the weather in a certain hour. For example, the nth index in every list represents data about the nth hour in the hours list given to you. The hours list tells you about the time and date of each data point. Each data point in a list corresponds to the data points in the other lists with the same index, since each index in the lists represents the same hour. Every element in the list represents a different hour in time. \n\nRespond by saying 'Optimal irrigation time: ', respond in short, and tell the user what date and time is optimal to irrigate, e.g. 21st of December at 14:00 or whatever the optimal time to irrigate is"
        },
        {
        "role": "user",
        "content": f"Predict the best time to irrigate a plant. Based on the following data only: List of hours: {timeList}, list of temperatures (degrees celcius): {temperatureHourlyList}, the list of wind speed in mph: {windHourlyList}, percipitation list (this is a number which multiplies the change of percipitation with the millimetres of percipitation): {compositePrecpitationList}, and lastly the humidity list: {humidityHourlyList} "
        }
    ],
    temperature=0.61,
    max_tokens=1665,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    clear_widgets(root)
    titleFrame = Frame(master = root).pack(pady = 25)
    titleResult1 = Label(text = "Optimal Irrigation Time", font = 'Cabrili 20 underline bold', master = titleFrame).pack(pady = 15)
    titleResult2 = Label(text = "in the Next 4 Days: ", font = 'Cabrili 20 underline bold', master = titleFrame).pack()


    labelResult = Label(text = str(openaiRESPONSE.choices[0].message.content[25:]), master = root, font = 'Cabrili 16 bold')
    labelResult.pack(pady = 200)



    # response is the response from the AI, make it so that it is shown to the user in the app!!!




def doneButtonPressed():
    # when the done button is pressed, we first try converting to decimal and see whether works. we check that the long and lat values are valid in terms of being converted to a float.
    global latitudeObj, longitudeObj, timeList, temperatureHourlyList, compositePrecpitationList, humidityHourlyList, windHourlyList
    clear_widgets(countryRegionWrongFrame)

    try:
        latitudeValue = float(latitudeObj.get())
        longitudeValue = float(longitudeObj.get())
    except ValueError:
        messagebox.showinfo("Error, TRY AGAIN", "Longitude and latitude values should be either a decimal or whole number. ")

    else:
        # now to check whether valid in terms of the value of them.


        if not -90.0 <= latitudeValue <= 90.0 :
            messagebox.showinfo("Error", "Latitude has to be between -90 and 90, try again. ")


        if not -180.0 <= longitudeValue <= 180.0:
            messagebox.showinfo("Error", "Longitude has to be between -180 and 180, try again.")


        if (-180 <= longitudeValue <= 180) and (-90 <= latitudeValue <= 90): # if valid:

            # sending the api request (getting actual weather). (will give us wind speed, weather and humidity). # 1000 free calls a day, i think up to 60 a minute but may be wrong, check.

            #### what is the alert response??? maybe the weather events?
            lat = latitudeValue
            long = longitudeValue
            ### do we want to exclude anything?? make sure fine right now with the empty value.
            ### standard units right now, fine??
            api_key_weather = 'weatherapi.com to get a key. ' 
            endpointWeather = f'http://api.weatherapi.com/v1/forecast.json?key={api_key_weather}&q={lat},{long}&days=4&alerts=yes'
            ### by default 4 days but will change later!! if u don't put anything for days then returns today's weathar.
            response = requests.get(endpointWeather)
            responseJSON = response.json()



            countryLabel = Label(text = f"Your country: {responseJSON['location']['country']}", master = countryRegionWrongFrame, font = 'Cabrili 16 bold')
            countryLabel.pack(pady = 25)

            regionLabel = Label(text = f"Your region: {responseJSON['location']['region']}", master = countryRegionWrongFrame, font = 'Cabrili 16 bold')
            regionLabel.pack(pady = 5)

            ifWrongLabel = Label(master = countryRegionWrongFrame, text = "If incorrect, retype longitude and latitude. ")
            ifWrongLabel.pack(pady = 10)


            correctButton = Button(master = countryRegionWrongFrame, text = "Correct", command = correct)
            correctButton.pack(pady = 5)

            # responseJSON keys are location current forecast and alerts.
            daysList = responseJSON['forecast']['forecastday']
            # daysList is a list of dictionaries, wehre every dictionary contains info about that day.
            # the keys are: 'date', 'date_epoch', 'day', 'astro', 'hour'
            timeList = []
            temperatureHourlyList = []
            windHourlyList = []
            compositePrecpitationList = []
            humidityHourlyList = []
            alertsReturned = responseJSON['alerts']
            # alertsReturned contains a dictionary where it's like alertsReturned = {alert: [here will go the details]}
            # what if there is more than one alert?
            print("ALERTS:", alertsReturned)

            for day in daysList: 
                for hour in day['hour']:
                    timeList.append(hour['time'])
                    temperatureHourlyList.append(hour['temp_c'])
                    windHourlyList.append(hour['wind_mph'])
                    chance = hour['chance_of_rain']
                    percipitation = hour['precip_mm']
                    compositePrecpitationList.append(chance * percipitation)
                    humidityHourlyList.append(hour['humidity'])
                    # now hour is a dictionary which describes an hour.
                    # keys: 'time_epoch', 'time', 'temp_c', 'temp_f', 'is_day', 'condition', 'wind_mph', 'wind_kph', 'wind_degree', 'wind_dir', 'pressure_mb', 'pressure_in', 'precip_mm', 'precip_in', 'humidity', 'cloud', 'feelslike_c', 'feelslike_f', 'windchill_c', 'windchill_f', 'heatindex_c', 'heatindex_f', 'dewpoint_c', 'dewpoint_f', 'will_it_rain', 'chance_of_rain', 'will_it_snow', 'chance_of_snow', 'vis_km', 'vis_miles', 'gust_mph', 'gust_kph', 'uv'

            print(responseJSON)
            print("\n\n\n\n\n\n")
            print(timeList)

















root = tk.Tk()
root.geometry('500x900')
root.configure(bg='light green')  # Set root window background color
title = Label(master = root, text = "Enter location: ", font = 'Cabrili 18 bold underline')
title.pack(pady = 50)

longlatFrame = tk.Frame(master = root)
longlatFrame.pack(pady = 50)

longFrame = tk.Frame(master = longlatFrame)
longFrame.pack(pady = 50)

latFrame = tk.Frame(master = longlatFrame)
latFrame.pack()

longitudeObj = tk.StringVar()
longitudeLabel = Label(master = longFrame, text = "Enter longitude(-180 to 180): ", font = "Cabrili 16")
longitudeLabel.pack(pady = 10)
longitudeEntry = Entry(master = longFrame, textvariable = longitudeObj)
longitudeEntry.pack()

latitudeObj = tk.StringVar()
latitudeLabel = Label(master = latFrame, text = "Enter latitude (-90 to 90): ", font = "Cabrili 16")
latitudeLabel.pack(pady = 10)
latitudeEntry = Entry(master = latFrame, textvariable = latitudeObj)
latitudeEntry.pack()

doneButton = Button(text = "Done", master = longlatFrame, command = doneButtonPressed)
doneButton.pack(pady = 50)



countryRegionWrongFrame = Frame(master = latFrame)
countryRegionWrongFrame.pack(pady = 20)

root.mainloop()
