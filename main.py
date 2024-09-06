import os
import sys
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import threading
import time
import logging

from astral import LocationInfo
from astral.sun import sun
import pytz
from datetime import datetime

import dateparser

from datetime import datetime, timedelta

from functools import wraps

class MainWindow(QWidget):

    _ui_width = 480
    _ui_height = 320

    def __init__(self):
        self.last_update_time = None
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(600000)  # 10 minutes in milliseconds

        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_cell)
        self.time_timer.start(1000)  # 1 second in milliseconds

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


    def update_cell(self, grid_layout, position, title, text, background_color=None):
        # Remove existing widget at the position if any
        if grid_layout.itemAtPosition(*position):
            existing_widget = grid_layout.itemAtPosition(*position).widget()
            existing_widget.setParent(None)
        label = QLabel(title+"\n"+text, self)
        label.setAlignment(Qt.AlignCenter)
        font = label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() * 2)  # Double the font size
        label.setFont(font)
        if background_color:
            label.setStyleSheet(f"background-color: {background_color.name()}; border: 1px solid black;")
        else:
            label.setStyleSheet("border: 1px solid black;")
        label.setFixedWidth(int(self._ui_width / 3))
        label.setFixedHeight(int(self._ui_height / 2))
        grid_layout.addWidget(label, *position)


    def datacell(self, position, title):
        def decorator(func):
            def wrapper(*args, **kwargs):
                #print(f"Decorator arguments: {arg1}, {arg2}")
                print("Before the function call")
                grid_layout = self.layout()
                try:
                    result, color = func(*args, **kwargs)
                    self.update_cell(grid_layout, position, title, result, color)

                except Exception as e:
                    logging.error(f"Error in {title}: {e}", exc_info=True)
                    self.update_cell(grid_layout, position, title, "Error", background_color=None)  # Green color
                    print("After the function call")

            return wrapper
        return decorator

    def initUI(self):
        self.setGeometry(100, 100, self._ui_width, self._ui_height)
        #self.setFixedSize(480, 320)
        #self.setMinimumSize(480, 320)
        #self.setMaximumSize(480, 320)
        self.setWindowTitle("PyQt5 Grid")

        # Set background color to light blue
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(211, 211, 211))  # Light grey color
        self.setPalette(palette)

        grid_layout = QGridLayout()
        #grid_layout.setSizeConstraint(QLayout.SetFixedSize)
        #grid_layout.setAlignment(Qt.AlignTop)
        #grid_layout.setSpacing(0)
        self.setLayout(grid_layout)

        titles = [
            "Launches", "Surf", "Sunrise/set"
        ]

        for i, title in enumerate(titles):
            self.update_cell(grid_layout, (0, i), title, "")

        #cell_texts = [
        #    "1 ^v", "2 ^v", "3 ^v",
        #    "4 ^v", "5 ^v", "6 ^v"
        #]
        cell_texts = ["Loading"] * 6
        positions = [(i, j) for i in range(2) for j in range(3)]

        for position, text in zip(positions, cell_texts):
            self.update_cell(grid_layout, position,"", text)

    #@@MainWindow.datacell( (0, 0), "Launches")
    def fetch_launches(self):
        @self.datacell((0, 0), "Launches")
        def fetch_launches():

            logging.info(f"Fetching launches at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            url = 'https://nextspaceflight.com/launches/nsf_launches/10/'
            response = requests.get(url)
            data = response.json()
            filtered_data = []
            tz = pytz.timezone('America/Los_Angeles')
            #now = datetime.now(tz)
            current_time = datetime.now(tz)
            for item in data:
                if any(loc in item['location'].lower() for loc in ['vandenberg', 'chica']):
                    #net_time = datetime.strptime(item['net'], '%Y-%m-%dT%H:%M:%SZ')
                    net_time = dateparser.parse(item['net'])
                    # 2024-09-06 13:38:13,562 - ERROR - Error in Launches: time data '2024-09-30T23:59:59.000059Z' does not match format '%Y-%m-%dT%H:%M:%SZ'



                    time_diff = net_time - current_time
                    days = time_diff.days
                    hours = time_diff.seconds // 3600
                    time_diff_str = f"{days}D {hours}H"
                    #filtered_data.append({'name': item['name'], 'net': item['net'], 'time_diff': time_diff_str})
                    filtered_data.append({'name': item['name'], 'net': net_time, 'time_diff': time_diff_str})
            logging.info(f"Fetched {len(filtered_data)} launches")
            #return filtered_data

            launches = filtered_data

            if launches:
                next_launch = launches[0]
                launch_text = f"{next_launch['name']}\n{next_launch['time_diff']}"
                days, hours = next_launch['time_diff'].split('D ')
                hours = int(hours[:-1])  # Remove the 'H' and convert to int
                if int(days) == 0 and hours < 12:
                    local_time = next_launch['net'].astimezone(tz).strftime("%I:%M")
                    launch_text = f"{next_launch['name']}\n{local_time}"

                    return launch_text, QColor(0, 255, 0)

                elif int(days) == 0 and hours < 20:
                    #self.update_cell(grid_layout, (0, 0), 'Launches', launch_text, background_color=QColor(0, 255, 0))  # Green color
                    return launch_text, QColor(0, 255, 0)
                else:
                    #self.update_cell(grid_layout, (0, 0), 'Launches', launch_text)
                    return launch_text, None
            else:
                #self.update_cell(grid_layout, (0, 0), 'Launches', 'None')
                return "None", None


                #return "Got Stuff", QColor(0, 255, 0)


            #raise Exception("Error in fetch_launches")
            #return "Got Stuff", None
        fetch_launches()
        return


    def fetch_surf(self):

        @self.datacell((0, 2), "Surf")
        def fetch_surf():

            url = 'https://surfcaptain.com/forecast/pacific-beach-california'
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Example parsing logic (you need to adjust this based on the actual HTML structure)
            surf_forecast = soup.select_one('#fcst-current-title')  # Select the <h1> element with id 'fcst-current-title'
            import re
            surf_forecast_text = surf_forecast.text if surf_forecast else 'N/A'  # Extract the text content
            logging.info(f"Surf forecast text: {surf_forecast_text}")
            match = re.search(r'(\d+)', surf_forecast_text)
            surf_forecast_formatted = f"{match.group(1)}FT" if match else 'N/A'  # Format the extracted value and unit
            logging.info(f"Formatted surf forecast: {surf_forecast_formatted}")

            surf_text = surf_forecast_formatted
            surf_height = float(surf_text.split('FT')[0]) if surf_text != 'N/A' else 0
            if surf_height >= 5:
                return surf_text, QColor(255, 0, 0)  # Red color
                #self.update_cell(grid_layout, (0, 2), 'Surf', surf_text, background_color=QColor(255, 0, 0))  # Red color
            elif surf_height >= 3:
                return surf_text, QColor(0, 255, 0)  # Green color
                #self.update_cell(grid_layout, (0, 2), 'Surf', surf_text, background_color=QColor(0, 255, 0))  # Green color
            else:
                #self.update_cell(grid_layout, (0, 2), 'Surf', surf_text)
                return surf_text, None
        fetch_surf()

    def fetch_wind(self):
        logging.info(f"Fetching wind data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        url = "https://api.weather.com/v2/pws/observations/current?apiKey=e1f10a1e78da46f5b10a1e78da96f525&stationId=KCASANDI141&numericPrecision=decimal&format=json&units=e"
        response = requests.get(url)
        data = response.json()

        if 'observations' in data and data['observations']:
            observation = data['observations'][0]
            wind_speed = int(observation['imperial']['windSpeed'])
            wind_gust = int(observation['imperial']['windGust'])
            wind_dir = observation['winddir']

            # Convert wind direction to cardinal direction
            dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            ix = round(wind_dir / 22.5) % 16
            cardinal_dir = dirs[ix]

            logging.info(f"Wind data fetched: {wind_speed}g{wind_gust} {cardinal_dir}")
            return {
                'speed': wind_speed,
                'gust': wind_gust,
                'direction': cardinal_dir
            }

        else:
            logging.warning("Failed to fetch wind data")
            return "N/A"

    def fetch_tidetimes(self):
        logging.info("Fetching tide times data")
        today_date = datetime.now().strftime('%Y%m%d')
        url = f"https://tidesandcurrents.noaa.gov/cgi-bin/stationtideinfo.cgi?Stationid=9410230&datum=MLLW&timezone=LST_LDT&units=english&clock=12hour&decimalPlaces=2&date={today_date}"
        response = requests.get(url)
        if response.status_code != 200:
            logging.warning("Failed to fetch tide times data")
            return "N/A"

        tide_data = response.text.splitlines()
        tide_events = []
        for line in tide_data:
            parts = line.split('|')
            if len(parts) == 3:
                time_str, height, event_type = parts
                tide_events.append((time_str, event_type))

        current_time = datetime.now()
        next_event = None
        for time_str, event_type in tide_events:
            time_str_dt = datetime.strptime(time_str, '%I:%M %p')
            current_time_str = current_time.strftime('%I:%M %p')
            current_time_dt = datetime.strptime(current_time_str, '%I:%M %p')
            logging.info(f"Comparing time_str: {time_str_dt} with current_time: {current_time_dt}")
            if time_str_dt > current_time_dt:
                next_event = (time_str, event_type)
                break

        if not next_event:
            # Fetch tomorrow's tide times if no upcoming tide events today
            tomorrow_date = (current_time + timedelta(days=1)).strftime('%Y%m%d')
            url = f"https://tidesandcurrents.noaa.gov/cgi-bin/stationtideinfo.cgi?Stationid=9410230&datum=MLLW&timezone=LST_LDT&units=english&clock=12hour&decimalPlaces=2&date={tomorrow_date}"
            response = requests.get(url)
            if response.status_code == 200:
                tide_data = response.text.splitlines()
                tide_events = []
                for line in tide_data:
                    parts = line.split('|')
                    if len(parts) == 3:
                        time_str, height, event_type = parts
                        tide_events.append((time_str, event_type))
                if tide_events:
                    next_time, next_type = tide_events[0]
                    next_event = (next_time, next_type)

        if next_event:
            next_time, next_type = next_event
            next_time_dt = datetime.strptime(next_time, '%I:%M %p')
            next_time_formatted = next_time_dt.strftime('%I:%M')  # Format without AM/PM
            next_type = next_type.strip()  # Remove leading and trailing spaces from next_type
            return f"{next_type.capitalize()}@{next_time_formatted}"
        else:
            return "No upcoming tide events"

    def fetch_tide(self):
        logging.info(f"Fetching tide data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        url = "https://api.tidesandcurrents.noaa.gov/api/prod//datagetter?&station=9410230&range=1&units=english&datum=MLLW&product=water_level&time_zone=LST_LDT&format=json&application=NOS.COOPS.TAC.COOPSMAP"
        response = requests.get(url)
        data = response.json()

        if 'data' in data and len(data['data']) >= 2:
            last_two_values = data['data'][-2:]
            last_value = float(last_two_values[-1]['v'])
            second_last_value = float(last_two_values[-2]['v'])

            trend = "rising" if last_value > second_last_value else "falling"
            logging.info(f"Tide data: Value: {last_value:.1f}Ft, Trend: {trend}")
            return {
                'value': last_value,
                'trend': trend
            }
        else:
            return {
                'value': 'N/A',
                'trend': 'N/A'
            }

    def fetch_sunriseset(self):

        @self.datacell((0, 1), "Sunrise/Set")
        def fetch_sunriseset():

            city = LocationInfo("San Diego", "California", "America/Los_Angeles", 32.7157, -117.1611)
            s = sun(city.observer, date=datetime.now().date(), tzinfo=city.timezone)

            current_time = datetime.now(tz=pytz.timezone(city.timezone))
            logging.info(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            next_sunrise = s['sunrise']
            next_sunset = s['sunset']

            if current_time > next_sunset:
                # If current time is after sunset, calculate sunrise for the next day
                next_day = datetime.now().date() + timedelta(days=1)
                s_next_day = sun(city.observer, date=next_day, tzinfo=city.timezone)
                next_event = 'sunrise'
                next_event_time = s_next_day['sunrise']
            elif next_sunrise > current_time and (next_sunset < current_time or next_sunrise < next_sunset):
                next_event = 'sunrise'
                next_event_time = next_sunrise
            else:
                next_event = 'sunset'
                next_event_time = next_sunset

            logging.info(f"Next event: {next_event}, Time: {next_event_time.strftime('%Y-%m-%d %H:%M:%S')}")

            sun_data = {
                'event': next_event,
                'time': next_event_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            #sun_data = self.fetch_sunriseset()
            event_symbol = '^' if sun_data['event'] == 'sunrise' else 'v'
            sun_time = sun_data['time'].split()[1][:5]  # Extract HH:MM part
            sun_text = f"{sun_time} {event_symbol}"
            return sun_text, None
            #self.update_cell(grid_layout, (0, 1), 'Sunrise/set', sun_text)

        fetch_sunriseset()

    def fetch_current_time(self):
        return datetime.now().strftime('%I:%M:%S')

    def update_data(self):
        # Move updating last_update_time to the end of the method

        # TODO: remove this once everything is converted.
        grid_layout = self.layout()

        self.fetch_launches()

        self.fetch_sunriseset()

        self.fetch_surf()

        tide_data = self.fetch_tide()
        tide_value = tide_data['value']
        tide_trend = tide_data['trend']
        tide_text = f"{tide_value:.1f}Ft {'v' if tide_trend == 'falling' else '^'}"
        tide_times_data = self.fetch_tidetimes()
        tide_text += f"\n{tide_times_data}"
        self.update_cell(grid_layout, (1, 0), 'Tide', tide_text)

        wind_data = self.fetch_wind()
        wind_text = f"{wind_data['speed']}g{wind_data['gust']} {wind_data['direction']}"
        if wind_data['speed'] >= 11:
            self.update_cell(grid_layout, (1, 1), 'Wind', wind_text, background_color=QColor(0, 255, 0))  # Green color
        else:
            self.update_cell(grid_layout, (1, 1), 'Wind', wind_text)

        self.last_update_time = datetime.now()  # Update last_update_time at the end

    def update_time_cell(self):
        try:
            grid_layout = self.layout()
            current_time = self.fetch_current_time()
            if self.last_update_time:
                elapsed_time = datetime.now() - self.last_update_time
                elapsed_seconds = int(elapsed_time.total_seconds())
                hours, remainder = divmod(elapsed_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                elapsed_time_str = f"Upd -{minutes}M"
            else:
                elapsed_time_str = "N/A"
            clock_text = f"{current_time}\n{elapsed_time_str}"
            self.update_cell(grid_layout, (1, 2), 'Clock', clock_text)

        except KeyboardInterrupt:
            print("Interrupted!")
            sys.exit(app.exec_())
            sys.exit(0)

if __name__ == '__main__':

    print(os.getpid())
    print(os.getppid())
    app = QApplication(sys.argv)
    main_window = MainWindow()
    #print(main_window.fetch_tidetimes())
    #sys.exit(0)
    #print(main_window.fetch_launches())
    #print(main_window.fetch_surf())
    print('showing main window')
    main_window.show()
    QTimer.singleShot(1000, main_window.update_data)  # No longer needed as the timer will handle updates
    sys.exit(app.exec_())

