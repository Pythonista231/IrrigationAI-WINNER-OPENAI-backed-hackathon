import requests
import tkinter as tk
from tkinter.ttk import *
from ttkbootstrap import Style
from tkinter import messagebox, filedialog
from openai import OpenAI
from PIL import Image, ImageTk
import base64
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import Canvas
import sys
import _tkinter



try:
    apiKey = ''
    client = OpenAI(api_key = apiKey)
except Exception as e: 
    messagebox.showerror("Error with openai service", f"Details {e}")
    sys.exit()


# clears the widgets of a frame. 
def clearWidgets(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def showProcessingScreen(frame):
    clearWidgets(frame)
    titleLabel = Label(master = frame, text = "Processing... This may take up to a minute ", font = 'calibri 18').pack(pady = 250)
    frame.update()

# called when root window is closed. 
def rootClosed(): # helps handle application termination. 
    global root2
    # this is called when the root window is closed. 
    try: 
        if not root2.winfo_exists(): # if root was closed but root2 is still open, don't terminate. 
            # if root was closed and root2 was also closed or doesn't exist, then terminate: 
            sys.exit()
    except NameError: # this occurs if root2 doesn't even exist yet, in which case terminate too. 
        sys.exit()
    except _tkinter.TclError: # this occurs if root2 has been closed, in which case terminate too. 
        sys.exit()

# called when root2 is closed. 
def root2Closed(): # helps handle application termination. 
    # if root2 is closed and root is also closed, then terminate the program, otherwise do nothing.
    try: 
        if not root.winfo_exists(): 
            sys.exit()
    except NameError: # this occurs if root2 doesn't even exist yet, in which case terminate too. 
        sys.exit()
    except _tkinter.TclError: # this occurs if root2 has been closed, in which case terminate too. 
        sys.exit()




# This function is executed first to ask user for a picture sample of crops to later establish the upper limit of the window of time available to choose the optimal irrigation from.
def getSamplePicture():
    global filePath

    # function to let them upload their sample of their crop. 
    def uploadImage(): 
        global filePath
        filePath = filedialog.askopenfilename(
            title = "Select a sample image of your crops", 
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if filePath: 
            if filePath.endswith((".jpg", ".jpeg", ".png")):
                try: 
                    img = Image.open(filePath)
                    img.thumbnail((400, 400))
                    img = ImageTk.PhotoImage(img)

                    imageLabel.config(image=img)
                    imageLabel.image = img
                except Exception as e: 
                    messagebox.showerror("Error, try again", f"Failed to open the image, details: {e}")
            else: 
                messagebox.showerror("Unsupported file type", "Only .png, .jpeg, .jpg file types are allowed.")

    clearWidgets(root)
    title = Label(root, text = "Enter a sample image of your crops", font = 'calibri 20 underline bold').pack(pady = 50, padx=20)

    uploadBtn = Button(root, text = "Upload Sample Image", command = uploadImage).pack(pady = 45)

    imageLabel = Label(root)
    imageLabel.pack(pady = 20)

    doneBtn = Button(root, text = "Done", command = calculateMaxDaysAvailable) # once get the picture call function to calculate num of days the plant can go without irrigation to establish an upper bound of a window from which to pinpoint optimal irrigation time. 

    doneBtn.pack(pady = 15)



#the image they uploaded is used to calculate the upper limit of the num of days available to irrigate. If the crop is in critical condition tells the user to irrigate now. 
# establishes a window from which the optimal irrigation time is picked. window size of possible irrigation times depends on current condition of plant. 
def calculateMaxDaysAvailable(): 
    global filePath, numDays
    #telling the user that the software is going to call an api and this may take a minute:
    showProcessingScreen(root)

    def encodeImage(filePath): 
        with open(filePath, "rb") as filePathFile: 
            return base64.b64encode(filePathFile.read()).decode('utf-8')
        
    # encoding. 
    base64Image = encodeImage(filePath)

    idx = filePath.rfind('.')
    imageType = filePath[idx + 1: ]
    
    # api call to GPT4V to calculate max days available to irrigate. 
    try:
        maxDaysAvailableResponse = client.chat.completions.create(

            model = 'gpt-4o', 
            messages = [
                {
                    "role": "system", 
                    "content": "You must look at the picture and respond with a single number like 1 or 2 or 3 or 4 or 21 whatever. The number represents the maximum number of days from now in which we can safely irrigate the plant. I have a program which tells you the optimal time to irrigate a plant, however for it to do that i need to first know from you a single number which represents the number of days from now wherein we should look at in terms of potential irrigation days to optimise. if you think that we should choose an irrigation time up to 8 days from now for example, then output 8. Don't pick a number lower than 1, don't pick a number higher than 14. Furthermore, if you feel like the plant is in critical condition and must be irrigated as soon as possible then just say IRRIGATE"
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": "look at the picture, give me a single number which describes how many days from now would be the max limit for the window in which you would look to find an optimal irrigation time. e.g. if the plant looks like it should be irrigated in the next 8 days, then tell me 8, and then later i will calculate an optimal irrigation time myself from now until that amount of days. If you think that the plant is in a critical condition and must be irrigated right now, then just say IRRIGATE"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{imageType};base64,{base64Image}"
                            }
                        }
                    ]
                }
            ], 
            temperature = 0.2, 
            frequency_penalty=0,
            presence_penalty=0

        )

        numDays = maxDaysAvailableResponse.choices[0].message.content.strip()
    except Exception as e: # in case there was an error. 
        messagebox.showerror("OPENAI API error:", f"{e}")
        sys.exit()

    

    if numDays.isnumeric(): 
        askLongLat() # ask longitude and latitude to find location and later gather location weather data. 

    else: 
        # this means that GPT4o said 'IRRIGATE' meaning critical condition, irrigate now. 
        numDays = "IRRIGATE"
        displayOptIrrigTime() # go straight to calling the display function instead of asking location and calculating optimal irrigation time. 
    


# after calculating the upper limit of the window of time available, ask the user their longitude and latitude to get their location and later get the weather data in their location. 
def askLongLat(): 
    global longitudeObj, latitudeObj, latFrame
    clearWidgets(root)
    
    title = Label(master = root, text = "Enter location: ", font = 'calibri 18 bold underline')
    title.pack(pady = 48, padx=20)

    longlatFrame = tk.Frame(master = root)
    longlatFrame.pack(pady = 40)

    longFrame = tk.Frame(master = longlatFrame)
    longFrame.pack(pady = 40)

    latFrame = tk.Frame(master = longlatFrame)
    latFrame.pack()

    longitudeObj = tk.StringVar()
    longitudeLabel = Label(master = longFrame, text = "Enter longitude(-180 to 180): ", font = "calibri 16")
    longitudeLabel.pack(pady = 10, padx = 20)
    longitudeEntry = Entry(master = longFrame, textvariable = longitudeObj)
    longitudeEntry.pack()

    latitudeObj = tk.StringVar()
    latitudeLabel = Label(master = latFrame, text = "Enter latitude (-90 to 90): ", font = "calibri 16")
    latitudeLabel.pack(pady = 10, padx = 20)
    latitudeEntry = Entry(master = latFrame, textvariable = latitudeObj)
    latitudeEntry.pack()

    doneButton = Button(text = "Done", master = longlatFrame, command = validateLongLatGetWeatherData) #once they press done validate their input and then get the weather data to be used to predict optimal irrigation time. 
    doneButton.pack(pady = 40, padx = 20)








        

# when press done after entering long and lat, this function validates their input as well as gathers the weather data at their location. 
def validateLongLatGetWeatherData():
    global longitudeObj, latitudeObj, countryRegionFrame, temperatureHourlyList, timeList, windHourlyList, humidityHourlyList, compositePrecipitationList, numDays, latFrame
    try: #first checking whether it is numerical data. 
        latitudeValue = float(latitudeObj.get())
        longitudeValue = float(longitudeObj.get())
    except ValueError:
        messagebox.showinfo("Error, please try again", "Longitude and latitude values should be either a decimal or whole number and nothing else. ")

    else: #if numerical data entered: 
        # now to check whether valid in terms of the value of the long and lat. 
        if not -90.0 <= latitudeValue <= 90.0 or not -180.0 <= longitudeValue <= 180.0:
            messagebox.showinfo("Error", "Longitude and latitude has to be between -90 and 90, try again. ")

        else: # if both the data is numeric and within the range, only thing remaining is validate with the user and get the weather data (this is done at the same time with the api request). 


            # sending the api request (getting actual weather). (will give us wind speed, weather and humidity).
            lat = latitudeValue
            long = longitudeValue
            api_key_weather = '' 
            try: 
                endpointWeather = f'http://api.weatherapi.com/v1/forecast.json?key={api_key_weather}&q={lat},{long}&days={numDays}&alerts=yes'
                weatherResponse = requests.get(endpointWeather)
                weatherResponseJSON = weatherResponse.json()

            except Exception as e: # in case an error occurs. 
                messagebox.showerror("Error with weather api", f"Details: {e}")
                sys.exit()

            # validating with them that their longitude and latitude correctly describe their location.
            countryRegionFrame = Frame(master = latFrame)
            countryRegionFrame.pack(pady = 20)
            countryLabel = Label(text = f"Your country: {weatherResponseJSON['location']['country']}", master = countryRegionFrame, font = 'calibri 16 bold', foreground = 'blue')
            countryLabel.pack(pady = 20, padx = 20)

            regionLabel = Label(text = f"Your region: {weatherResponseJSON['location']['region']}", master = countryRegionFrame, font = 'calibri 16 bold', foreground = 'blue')
            regionLabel.pack(pady = 5, padx = 20)

            ifWrongLabel = Label(master = countryRegionFrame, text = "If incorrect, re-enter Longitude and Latitude & click 'Done'. ", wraplength=550, anchor="center",  justify="center")
            ifWrongLabel.pack(pady = 10, padx = 20)

            # user clicks correct if true, re enters & clicks done again if not. 
            correctButton = Button(master = countryRegionFrame, text = "Correct", command = calculateOptIrrigTime) # once finished calculate the optimal irrigation time with the weather data and the time window available. 
            correctButton.pack(pady = 5)

            # response data manipulation: 
            # weatherResponseJSON keys are location current forecast and alerts.
            daysList = weatherResponseJSON['forecast']['forecastday']
            # daysList is a list of dictionaries, wehre every dictionary contains info about that day.
            # the keys are: 'date', 'date_epoch', 'day', 'astro', 'hour'
            timeList = []
            temperatureHourlyList = []
            windHourlyList = []
            compositePrecipitationList = []
            humidityHourlyList = []
            alertsReturned = weatherResponseJSON['alerts']
            print("ALERTS:", alertsReturned)

            for day in daysList: 
                for hour in day['hour']:
                    timeList.append(hour['time'])
                    temperatureHourlyList.append(hour['temp_c'])
                    windHourlyList.append(hour['wind_mph'])
                    chance = hour['chance_of_rain']
                    precipitation = hour['precip_mm']
                    compositePrecipitationList.append(chance * precipitation)
                    humidityHourlyList.append(hour['humidity'])
                    # now hour is a dictionary which describes an hour.
                    # keys: 'time_epoch', 'time', 'temp_c', 'temp_f', 'is_day', 'condition', 'wind_mph', 'wind_kph', 'wind_degree', 'wind_dir', 'pressure_mb', 'pressure_in', 'precip_mm', 'precip_in', 'humidity', 'cloud', 'feelslike_c', 'feelslike_f', 'windchill_c', 'windchill_f', 'heatindex_c', 'heatindex_f', 'dewpoint_c', 'dewpoint_f', 'will_it_rain', 'chance_of_rain', 'will_it_snow', 'chance_of_snow', 'vis_km', 'vis_miles', 'gust_mph', 'gust_kph', 'uv'





# this is called after we have established how long of a window is open to choose the optimal irrigation time from. this isn't called if the plant is in critical condition. 
def calculateOptIrrigTime():
    global numDays, temperatureHourlyList, timeList, windHourlyList, humidityHourlyList, compositePrecipitationList, openaiResponse

    # telling the user that this may take some time to process: 
    showProcessingScreen(root)


    numDays = int(numDays)

    # once they give a picture and have established how many days we have, we use the weather data we obtained to calculate an optimal irrigation time. 
    try: 
        openaiResponse = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
            "role": "system",
            "content": "You are an expert at crop irrigation and agriculture. After many years of experience in farming of all sorts of crops, you know how to find the optimal time for irrigation of a crop based on climate data that is given to you. Each list describes a different data point. Each element in a list represents information about the weather in a certain hour. For example, the nth index in every list represents data about the nth hour in the hours list given to you. The hours list tells you about the time and date of each data point. Each data point in a list corresponds to the data points in the other lists with the same index, since each index in the lists represents the same hour. Every element in the list represents a different hour in time. \n\nRespond only by saying one of the values in the list of hours and nothing else! e.g. 2023-12-24 19:00"
            },
            {
            "role": "user",
            "content": f"Predict the best time to irrigate a plant. Based on the following data only: List of hours: {timeList}, list of temperatures (degrees celsius): {temperatureHourlyList}, the list of wind speed in mph: {windHourlyList}, precipitation list (this is a number which multiplies the change of precipitation with the millimetres of precipitation): {compositePrecipitationList}, and lastly the humidity list: {humidityHourlyList} "
            }
        ],
        temperature=0.2,
        max_tokens=1665,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
    except Exception as e: # in case an exception occured. 
        messagebox.showerror("Error with openai API", f"Details: {e}")
        sys.exit()
    displayOptIrrigTime(openaiResponse) # call display function to show the user the optimal irrigation time. 


#displays the optimal irrigation time to the user, if in critical condition displays IRRIGATE NOW - CRITICAL CONDITION. 
def displayOptIrrigTime(openaiResponse = False): #by default openaiResponse is false meaning in which case then the plant is in critical condition. if openaiResponse was a string then it wasn't in critical condition. 
    clearWidgets(root)

    if openaiResponse: 
    
        # showing the optimal irrigation time to the user: 
        titleFrame = Frame(master = root).pack(pady = 15, padx = 20)
        titleResult1 = Label(text = "Optimal Irrigation Time", font = 'calibri 20 underline bold', master = titleFrame, wraplength=550, anchor="center",  justify="center").pack(pady = 50)

        titleResult2 = Label(text = f"Based on the condition of the crop, we estimated that there is a window of {numDays} in which to pinpoint the optimal irrigation time. ", font = 'calibri 15 bold', wraplength=550, anchor="center",  justify="center").pack(pady = 15)

        titleResult3 = Label(text = f"The optimal irrigation time within the next {numDays} days: ", font = 'calibri 15 bold', master = titleFrame, wraplength=550, anchor="center",  justify="center").pack(pady = 30)

        labelResult = Label(text = str(openaiResponse.choices[0].message.content), master = root, font = 'calibri 18 bold', wraplength=550, anchor="center",  justify="center", foreground='blue')
        labelResult.pack(pady = 130)


        analysisBtn = Button(root, text = "More Info / View Data Analysed", command = showData, width=30).pack(pady = 45)


    else: 
        titleFrame = Frame(master = root).pack(pady = 15, padx = 20)
        titleResult1 = Label(text = "Optimal Irrigation Time", font = 'calibri 20 underline bold', master = titleFrame, wraplength=550, anchor="center",  justify="center").pack(pady = 50)
        titleResult2 = Label(text = f"Based on the sample photo provided, the plant is in critical condition and ought to be irrigated immediately. ", font = 'calibri 15 bold', wraplength=550, anchor="center",  justify="center").pack(pady = 15)
        titleResult3 = Label(text = f"Waiting for an optimal irrigation time will likely be counterproductive, given the visible water stress. ", font = 'calibri 15 bold', master = titleFrame, wraplength=550, anchor="center",  justify="center").pack(pady = 130)

        







def showData(): # this is a function to show the user the weather data of all the days which were part of the window of time the optimal irrigation time was chosen from. 
    global openaiResponse, root2

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
    root2 = tk.Tk()
    root2.title("Weather Data Plots")

    root2.geometry('1600x1000')

    frame2 = Frame(root2)
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
    plotFrame = Frame(canvas)
    canvas.create_window((0, 0), window=plotFrame, anchor='nw')

    #plotting each datapoint in a graph. 
    # the width of the graphs depend on how large the irrigation window that was taken into consideration was: 
    width = 0.20 * len(timeList)
    fig, axs = plt.subplots(4, 1, figsize=(width, 10))  # 4 subplots 

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

    canvas_fig = FigureCanvasTkAgg(fig, master=plotFrame)
    canvas_fig.draw()
    canvas_fig.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # updating the scroll region: 
    plotFrame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    root2.lift() # brings up the analysis window so user won't have to find it. 
    root2.attributes("-topmost", True)
    root2.protocol("WM_DELETE_WINDOW", lambda: (root2.destroy(), root2Closed())) # helps handle application termination. 
    root2.mainloop()

















# starting view:

root = tk.Tk()
root.geometry('700x800')

getSamplePicture() #the first thing that is done is asking for a sample picture of the crops. This is to assess its condition in order to determine what window size is available to choose the opt. irrig time from

root.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), rootClosed())) # helps handle application termination. 
root.lift() # brings up the window so user won't have to find it. 
root.attributes("-topmost", True)


root.mainloop()
