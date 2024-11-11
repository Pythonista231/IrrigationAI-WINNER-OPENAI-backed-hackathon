import requests
import tkinter as tk
from tkinter.ttk import *
from ttkbootstrap import Style
from tkinter import messagebox
from openai import OpenAI
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import Canvas
import sys



print("**INTERNAL BACK TESTING SOFTWARE**\n\n")


def newLines(n): 
    for i in range(n): 
        print("")


def rootClosed(): # handles software termination. 
    sys.exit()



# function to gather weather data from their location. returns response in json. 
def getWeatherData(longitude, latitude): 
    # getting their weather data: 
    apiKeyWeather = 'enter your weather api key from weatherapi.com here'
    endpointWeather = f'http://api.weatherapi.com/v1/forecast.json?key={apiKeyWeather}&q={latitude},{longitude}&days=3&alerts=yes'
    # since this software is used for testing, we use a default value of 3 for the number of days from now in which irrigation could take place. 
    # in the actual software (not this testing software), a photo sample of a crop is taken to establish the max number of days from now irrigation could be delayed, so that we can choose an optimal irrigation time from that window.  
    try: 

        weatherResponse = requests.get(endpointWeather)
        weatherResponseJSON = weatherResponse.json()
        return weatherResponseJSON
    except Exception as e: 
        messagebox.showerror("Error with weather api", f"Details: {e}")
        sys.exit()



# function to calculate optimal irrigation time. returns plain response with no modification
def calculateOptIrrigTime(timeList, temperatureHourlyList, windHourlyList, humidityHourlyList, compositePrecipitationList): 
    try: 
        openaiKey = 'enter your openai api key here'
        client = OpenAI(api_key=openaiKey)
        # api call to calculate optimal irrigation time. 
        openaiResponse = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                "role": "system",
                "content": "You are an expert at crop irrigation and agriculture. After many years of experience in farming of all sorts of crops, you know how to find the optimal time for irrigation of a crop based on climate data that is given to you. Each list describes a different data point. Each element in a list represents information about the weather in a certain hour. For example, the nth index in every list represents data about the nth hour in the hours list given to you. The hours list tells you about the time and date of each data point. Each data point in a list corresponds to the data points in the other lists with the same index, since each index in the lists represents the same hour. Every element in the list represents a different hour in time. \n\nRespond only by saying one of the values in the list of hours and nothing else, e.g. '2023-12-24 19:00'"
                },
                {
                "role": "user",
                "content": f"Predict the single best time to irrigate a plant. Based on the following data only: List of hours: {timeList}, list of temperatures (degrees celsius): {temperatureHourlyList}, the list of wind speed in mph: {windHourlyList}, precipitation list (this is a number which multiplies the change of precipitation with the millimetres of precipitation): {compositePrecipitationList}, and lastly the humidity list: {humidityHourlyList} "
                }
            ],
            temperature=0.2, 
            frequency_penalty=0,
            presence_penalty=0
            )  
    except Exception as e: 
        messagebox.showerror("Error with openai api", f"Details: {e}")
    return openaiResponse






# getting long and lat from user: 
latitude = input("Enter your latitude: ")
longitude = input("Enter your longitude: ")


weatherResponseJSON = getWeatherData(longitude, latitude) #getting their weather data. 
newLines(2)

# telling the user the location they entered. 
print(f"Your country: {weatherResponseJSON['location']['country']}")
newLines(1)
print(f"Your region: {weatherResponseJSON['location']['region']}")
newLines(4)

# computations on JSON response gotten from weather api. 
daysList = weatherResponseJSON['forecast']['forecastday']
timeList = []
temperatureHourlyList = []
windHourlyList = []
compositePrecipitationList = []
humidityHourlyList = []
alertsReturned = weatherResponseJSON['alerts']
print("ALERTS:", alertsReturned)
newLines(4)

for day in daysList: 
    for hour in day['hour']:
        timeList.append(hour['time'])
        temperatureHourlyList.append(hour['temp_c'])
        windHourlyList.append(hour['wind_mph'])
        chance = hour['chance_of_rain']
        precipitation = hour['precip_mm']
        compositePrecipitationList.append(chance * precipitation)
        humidityHourlyList.append(hour['humidity'])




# getting optimal irrigation time: 
openaiResponse = calculateOptIrrigTime(timeList, temperatureHourlyList, windHourlyList, humidityHourlyList, compositePrecipitationList)

# showing user optimal irrigation time: 
print(f"The optimal time to irrigate is: {openaiResponse.choices[0].message.content}")
print("Please find the opened window contianing the data plotted in graphs. ")
element = openaiResponse.choices[0].message.content
elementList = element.split(' ')
beforeSpace = elementList[0]
afterSpace = elementList[1]
elementDate = beforeSpace.split('-')[2]
elementTime = afterSpace.split(':')[0]
if elementTime[0] == '0' and elementTime != '00':
    elementTime = elementTime[1]
result = f'{elementDate}\n@\n{elementTime}'


# plotting graphs for analysis (back-testing for evaluation and validation of optimal irrigation time result): 
newXAxisLabels = []
for element in timeList: 
    elementList = element.split(' ')
    beforeSpace = elementList[0]
    afterSpace = elementList[1]
    elementDate = beforeSpace.split('-')[2]
    elementTime = afterSpace.split(':')[0]
    if elementTime[0] == '0' and elementTime != '00':
        elementTime = elementTime[1]
    newXAxisLabels.append(f'{elementDate}\n@\n{elementTime}')



# tkinter: 
root = tk.Tk()
root.title("Weather Data Plots")

root.geometry('1600x1000')

frame2 = Frame(root)
frame2.pack(fill=tk.BOTH, expand=True)

# scrollbar: 
scrollbarVertical = Scrollbar(frame2, orient = tk.VERTICAL)
scrollbarVertical.pack(side=tk.RIGHT, fill=tk.Y)

scrollbarHorizontal = Scrollbar(frame2, orient = tk.HORIZONTAL)
scrollbarHorizontal.pack(side = tk.BOTTOM, fill = tk.X)

# canvas holds the plots: 
canvas = Canvas(frame2, yscrollcommand=scrollbarVertical.set, xscrollcommand=scrollbarHorizontal.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbarVertical.config(command=canvas.yview)
scrollbarHorizontal.config(command=canvas.xview)

# intuitive scrolling capability: 
canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * (event.delta // 120), "units"))
canvas.bind_all("<Shift-MouseWheel>", lambda event: canvas.xview_scroll(-1 * (event.delta // 120), "units"))


# frame to hold plots inside canvas: 
plot_frame = Frame(canvas)
canvas.create_window((0, 0), window=plot_frame, anchor='nw')

#plotting each datapoint in a graph. 
# the width of the graphs depend on how large the irrigation window that was taken into consideration was: 
width = 0.20 * len(timeList)
fig, axs = plt.subplots(4, 1, figsize=(width, 10))  # 4 subplots 

# 4 plots. 

axs[0].plot(newXAxisLabels, temperatureHourlyList, marker='X')
axs[0].set_xlabel('All hours in irrigation window')
axs[0].set_ylabel('Temperature C')
axs[0].set_title('Temperatures graph', color = 'blue')
axs[0].grid(True)
axs[0].axvline(result, color='red', linestyle='--', label='Optimal Irrigation Time Predicted')
axs[0].legend(loc='upper right')  
axs[0].text(0, 0, '\n***X AXIS: Date@Time', transform=axs[0].transAxes, va='bottom', ha='left', fontsize=10, color = 'red')


axs[1].plot(newXAxisLabels, windHourlyList, marker='X')
axs[1].set_xlabel('All hours in irrigation window')
axs[1].set_ylabel('Wind mph')
axs[1].set_title('Wind speed graph', color = 'blue')
axs[1].grid(True)
axs[1].axvline(result, color='red', linestyle='--', label='Optimal Irrigation Time Predicted')
axs[1].legend(loc='upper right')  


axs[2].plot(newXAxisLabels, compositePrecipitationList, marker='X')
axs[2].set_xlabel('All hours in irrigation window')
axs[2].set_ylabel('Precipitation (mm * chance of rain)')
axs[2].set_title('Precipitation graph', color = 'blue')
axs[2].grid(True)
axs[2].axvline(result, color='red', linestyle='--', label='Optimal Irrigation Time Predicted')
axs[2].legend(loc='upper right')  

axs[3].plot(newXAxisLabels, humidityHourlyList, marker='X')
axs[3].set_xlabel('All hours in irrigation window')
axs[3].set_ylabel('Humidity')
axs[3].set_title('Humidity graph', color = 'blue')
axs[3].grid(True)
axs[3].axvline(result, color='red', linestyle='--', label='Optimal Irrigation Time Predicted')
axs[3].legend(loc='upper right')  



for ax in axs:
    ax.tick_params(axis='x', labelsize=7)

plt.tight_layout()

canvas_fig = FigureCanvasTkAgg(fig, master=plot_frame)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# updating the scroll region: 
plot_frame.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))


root.lift() # brings up the analysis window so user won't have to find it. 
root.focus_force()
root.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), rootClosed())) # handles application termination. 
root.mainloop()
