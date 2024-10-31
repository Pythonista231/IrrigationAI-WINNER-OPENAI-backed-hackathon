import requests
import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from ttkbootstrap import Style
from openai import OpenAI



apiKey = 'OPENAI API KEY'
client = OpenAI(api_key = apiKey)


def clearWidgets(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def correctPressedCalcOptIrrigTime():
    global openaiResponse, temperatureHourlyList, timeList, windHourlyList, humidityHourlyList, compositePrecipitationList
    # once they click the correct button, this is executed which calculates the result of the optimal irrigation time. 

    openaiResponse = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
        "role": "system",
        "content": "You are an expert at crop irrigation and agriculture. After many years of experience in farming of all sorts of crops, you know how to find the optimal time for irrigation of a crop based on climate data that is given to you. Each list describes a different data point. Each element in a list represents information about the weather in a certain hour. For example, the nth index in every list represents data about the nth hour in the hours list given to you. The hours list tells you about the time and date of each data point. Each data point in a list corresponds to the data points in the other lists with the same index, since each index in the lists represents the same hour. Every element in the list represents a different hour in time. \n\nRespond by saying 'Optimal irrigation time: ', respond in short, and tell the user what date and time is optimal to irrigate, e.g. 21st of December at 14:00 or whatever the optimal time to irrigate is"
        },
        {
        "role": "user",
        "content": f"Predict the best time to irrigate a plant. Based on the following data only: List of hours: {timeList}, list of temperatures (degrees celcius): {temperatureHourlyList}, the list of wind speed in mph: {windHourlyList}, percipitation list (this is a number which multiplies the change of percipitation with the millimetres of percipitation): {compositePrecipitationList}, and lastly the humidity list: {humidityHourlyList} "
        }
    ],
    temperature=0.61,
    max_tokens=1665,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )



def displayOptIrrigTime(): 
    global openaiResponse
    # this function is called after the one above which calculates it. This function displays the optimal irrigation time to the user. 
    clearWidgets(root)
    
    # showing the optimal irrigation time to the user: 
    titleFrame = Frame(master = root).pack(pady = 25)
    titleResult1 = Label(text = "Optimal Irrigation Time", font = 'Cabrili 20 underline bold', master = titleFrame).pack(pady = 15)
    titleResult2 = Label(text = "in the Next 4 Days: ", font = 'Cabrili 20 underline bold', master = titleFrame).pack()


    labelResult = Label(text = str(openaiResponse.choices[0].message.content[25:]), master = root, font = 'Cabrili 16 bold')
    labelResult.pack(pady = 200)








def donePressedGetWeatherData():
    global temperatureHourlyList, timeList, windHourlyList, humidityHourlyList, compositePrecipitationList
    # when the done button is pressed, we use their longitude and latitude values to gather data about their weather. 
    # also validates their inputs and confirms the user's location with the user.  
    clearWidgets(countryRegionWrongFrame)

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

            # sending the api request (getting actual weather). (will give us wind speed, weather and humidity).

            lat = latitudeValue
            long = longitudeValue
            api_key_weather = 'weatherapi.com to get a key. ' 
            endpointWeather = f'http://api.weatherapi.com/v1/forecast.json?key={api_key_weather}&q={lat},{long}&days=4&alerts=yes'
            response = requests.get(endpointWeather)
            responseJSON = response.json()


            countryLabel = Label(text = f"Your country: {responseJSON['location']['country']}", master = countryRegionWrongFrame, font = 'Cabrili 16 bold')
            countryLabel.pack(pady = 25)

            regionLabel = Label(text = f"Your region: {responseJSON['location']['region']}", master = countryRegionWrongFrame, font = 'Cabrili 16 bold')
            regionLabel.pack(pady = 5)

            ifWrongLabel = Label(master = countryRegionWrongFrame, text = "If incorrect, retype longitude and latitude. ")
            ifWrongLabel.pack(pady = 10)


            correctButton = Button(master = countryRegionWrongFrame, text = "Correct", command = correctPressedCalcOptIrrigTime)
            correctButton.pack(pady = 5)

            # responseJSON keys are location current forecast and alerts.
            daysList = responseJSON['forecast']['forecastday']
            # daysList is a list of dictionaries, wehre every dictionary contains info about that day.
            # the keys are: 'date', 'date_epoch', 'day', 'astro', 'hour'
            timeList = []
            temperatureHourlyList = []
            windHourlyList = []
            compositePrecipitationList = []
            humidityHourlyList = []
            alertsReturned = responseJSON['alerts']
            print("ALERTS:", alertsReturned)

            for day in daysList: 
                for hour in day['hour']:
                    timeList.append(hour['time'])
                    temperatureHourlyList.append(hour['temp_c'])
                    windHourlyList.append(hour['wind_mph'])
                    chance = hour['chance_of_rain']
                    percipitation = hour['precip_mm']
                    compositePrecipitationList.append(chance * percipitation)
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

doneButton = Button(text = "Done", master = longlatFrame, command = donePressedGetWeatherData)
doneButton.pack(pady = 50)



countryRegionWrongFrame = Frame(master = latFrame)
countryRegionWrongFrame.pack(pady = 20)

root.mainloop()
