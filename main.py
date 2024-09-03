import os
import sys
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import threading
import time

from datetime import datetime

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()


    def update_cell(self, grid_layout, position, title, text):
        # Remove existing widget at the position if any
        if grid_layout.itemAtPosition(*position):
            existing_widget = grid_layout.itemAtPosition(*position).widget()
            existing_widget.setParent(None)
        label = QLabel(title+"\n"+text, self)
        grid_layout.addWidget(label, *position)

    def initUI(self):
        self.setGeometry(100, 100, 300, 200)
        self.setWindowTitle("PyQt5 Grid")

        grid_layout = QGridLayout()
        self.setLayout(grid_layout)

        titles = [
            "Launches", "Surf", "Sunrise/set"
        ]

        for i, title in enumerate(titles):
            self.update_cell(grid_layout, (0, i), title, "")

        cell_texts = [
            "1 ^v", "2 ^v", "3 ^v",
            "4 ^v", "5 ^v", "6 ^v"
        ]

        positions = [(i, j) for i in range(2) for j in range(3)]

        for position, text in zip(positions, cell_texts):
            self.update_cell(grid_layout, position,"", text)

    def fetch_launches(self):
        url = 'https://nextspaceflight.com/launches/nsf_launches/10/'
        response = requests.get(url)
        data = response.json()
        filtered_data = []
        current_time = datetime.now()
        for item in data:
            if 'vandenberg' in item['location'].lower():
                net_time = datetime.strptime(item['net'], '%Y-%m-%dT%H:%M:%SZ')
                time_diff = net_time - current_time
                days = time_diff.days
                hours = time_diff.seconds // 3600
                time_diff_str = f"{days}D {hours}H"
                filtered_data.append({'name': item['name'], 'net': item['net'], 'time_diff': time_diff_str})
        return filtered_data

    def fetch_surf(self):
        url = 'https://surfcaptain.com/forecast/pacific-beach-california'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Example parsing logic (you need to adjust this based on the actual HTML structure)
        surf_forecast = soup.select_one('#fcst-current-title')  # Select the <h1> element with id 'fcst-current-title'
        import re
        surf_forecast_text = surf_forecast.text if surf_forecast else 'N/A'  # Extract the text content
        match = re.search(r'(\d+)\s*ft', surf_forecast_text, re.IGNORECASE)
        surf_forecast_formatted = f"{match.group(1)}FT" if match else 'N/A'  # Format the extracted value and unit

        return {
            'surf_forecast': surf_forecast_formatted
        }

    def fetch_tide(self):
        url = "https://api.tidesandcurrents.noaa.gov/api/prod//datagetter?&station=9410230&range=1&units=english&datum=MLLW&product=water_level&time_zone=LST_LDT&format=json&application=NOS.COOPS.TAC.COOPSMAP"
        response = requests.get(url)
        data = response.json()

        if 'data' in data and len(data['data']) >= 2:
            last_two_values = data['data'][-2:]
            last_value = float(last_two_values[-1]['v'])
            second_last_value = float(last_two_values[-2]['v'])

            trend = "rising" if last_value > second_last_value else "falling"
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
        from astral import LocationInfo
        from astral.sun import sun
        import pytz
        from datetime import datetime

        city = LocationInfo("San Diego", "California", "America/Los_Angeles", 32.7157, -117.1611)
        s = sun(city.observer, date=datetime.now().date(), tzinfo=city.timezone)

        current_time = datetime.now(tz=pytz.timezone(city.timezone))
        next_sunrise = s['sunrise']
        next_sunset = s['sunset']

        if next_sunrise > current_time and (next_sunset < current_time or next_sunrise < next_sunset):
            next_event = 'sunrise'
            next_event_time = next_sunrise
        else:
            next_event = 'sunset'
            next_event_time = next_sunset

        return {
            'event': next_event,
            'time': next_event_time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def update_data(self):

        grid_layout = self.layout()

        launches = self.fetch_launches()
        if launches:
            next_launch = launches[0]
            launch_text = f"{next_launch['name']}\n{next_launch['time_diff']}"
        else:
            launch_text = 'None'
        self.update_cell(grid_layout, (0, 0), 'Launches', launch_text)

        surf_data = self.fetch_surf()
        surf_text = surf_data['surf_forecast']
        self.update_cell(grid_layout, (0, 1), 'Surf', surf_text)

        sun_data = self.fetch_sunriseset()
        event_symbol = '^' if sun_data['event'] == 'sunrise' else 'v'
        sun_time = sun_data['time'].split()[1][:5]  # Extract HH:MM part
        sun_text = f"{sun_time} {event_symbol}"
        self.update_cell(grid_layout, (0, 2), 'Sunrise/set', sun_text)

        tide_data = self.fetch_tide()
        tide_value = tide_data['value']
        tide_trend = tide_data['trend']
        tide_text = f"{tide_value:.1f}Ft {'v' if tide_trend == 'falling' else '^'}"
        self.update_cell(grid_layout, (1, 0), 'Tide', tide_text)

if __name__ == '__main__':

    print(os.getpid())
    print(os.getppid())
    app = QApplication(sys.argv)
    main_window = MainWindow()
    #print(main_window.fetch_tide())
    #sys.exit(0)
    #print(main_window.fetch_launches())
    #print(main_window.fetch_surf())
    print('showing main window')
    main_window.show()
    QTimer.singleShot(5000, main_window.update_data)
    sys.exit(app.exec_())
