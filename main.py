import sys
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from datetime import datetime

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 300, 200)
        self.setWindowTitle("PyQt5 Grid")

        grid_layout = QGridLayout()
        self.setLayout(grid_layout)

        launches = self.fetch_launches()
        launches = self.fetch_launches()
        if launches:
            next_launch = launches[0]
            cell_texts = [
                f"{next_launch['name']}\n{next_launch['time_diff']}", "2 ^v", "3 ^v",
                "4 ^v", "5 ^v", "6 ^v"
            ]
        else:
            cell_texts = [
                "none", "2 ^v", "3 ^v",
                "4 ^v", "5 ^v", "6 ^v"
            ]

        positions = [(i, j) for i in range(2) for j in range(3)]

        for position, text in zip(positions, cell_texts):
            label = QLabel(text, self)
            grid_layout.addWidget(label, *position)

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

        # Extract and format the data
        #low_tide = tide_data[0].text if tide_data else 'N/A'
        #high_tide = tide_data[1].text if len(tide_data) > 1 else 'N/A'
        #wind_speed = wind_data[0].text if wind_data else 'N/A'

        return {
            'surf_forecast': surf_forecast_formatted
            #'low_tide': low_tide,
            #'high_tide': high_tide,
            #'wind_speed': wind_speed
        }

if __name__ == '__main__':

    app = QApplication(sys.argv)
    main_window = MainWindow()
    print(main_window.fetch_surf())
    main_window.show()
    sys.exit(app.exec_())
