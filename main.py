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
import subprocess
import platform
import socket

from astral import LocationInfo
from astral.sun import sun
import pytz
from datetime import datetime

import dateparser

from datetime import datetime, timedelta

from functools import wraps

import psutil

class MainWindow(QWidget):

    _ui_width = 480
    _ui_height = 320

    _color_green = QColor(0, 255, 0)
    _color_yellow = QColor(255, 255, 0)
    _color_red = QColor(255, 0, 0)
    _color_orange = QColor(255, 128, 0)
    _color_light_blue = QColor(173, 216, 230)  # Light blue for rain indication

    _fudge = 12

    def __init__(self):
        self.last_update_time = None
        super().__init__()
        # Initialize DataStore to hold all fetched data
        self.data_store = {
            'launches': [],
            'surf': None,
            'wind': None,
            'tide': None,
            'tide_times': None,
            'sunriseset': None,
            'nws': None,
            'last_update': None
        }
        self.overlay = None
        self.overlay_visible = False
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(600000)  # 10 minutes in milliseconds

        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_cell)
        self.time_timer.start(1000)  # 1 second in milliseconds

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


    def update_cell(self, grid_layout, position, title, text, background_color=None, clickable=False, click_callback=None):
        # Remove existing widget at the position if any
        if grid_layout.itemAtPosition(*position):
            existing_widget = grid_layout.itemAtPosition(*position).widget()
            existing_widget.setParent(None)
        label = QLabel(title+"\n"+text, self)
        label.setAlignment(Qt.AlignCenter)
        font = label.font()
        font.setBold(True)
        font.setPointSize(int(font.pointSize() * 1.5))  # Double the font size
        label.setFont(font)
        if isinstance(background_color, str):
            background_color = QColor(background_color)

        if background_color:
            label.setStyleSheet(f"background-color: {background_color.name()}; border: 1px solid black;")
        else:
            label.setStyleSheet("border: 1px solid black;")
        label.setFixedWidth(int(self._ui_width / 3) - self._fudge)
        label.setFixedHeight(int(self._ui_height / 2) - self._fudge)

        if clickable and click_callback:
            label.mousePressEvent = lambda e: click_callback()
            label.setCursor(Qt.PointingHandCursor)

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

    def fetch_launches(self):
        """Fetch launch data and return raw data structure"""
        logging.info(f"Fetching launches at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        url = 'https://nextspaceflight.com/launches/nsf_launches/10/'
        response = requests.get(url)
        data = response.json()
        filtered_data = []
        tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(tz)
        for item in data:
            if any(loc in item['location'].lower() for loc in ['vandenberg', 'chica']):
                net_time = dateparser.parse(item['net'])
                time_diff = net_time - current_time
                days = time_diff.days
                hours = time_diff.seconds // 3600
                time_diff_str = f"{days}D {hours}H"
                filtered_data.append({
                    'name': item['name'],
                    'net': net_time,
                    'time_diff': time_diff_str,
                    'time_diff_days': days,
                    'time_diff_hours': hours
                })
        logging.info(f"Fetched {len(filtered_data)} launches")
        return filtered_data


    def fetch_surf(self):
        """Fetch surf data and return raw data structure"""
        url = 'https://surfcaptain.com/forecast/pacific-beach-california'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        surf_forecast = soup.select_one('#fcst-current-title')
        import re
        surf_forecast_text = surf_forecast.text if surf_forecast else 'N/A'
        logging.info(f"Surf forecast text: {surf_forecast_text}")
        match = re.search(r'([\d\-\+]+)', surf_forecast_text)
        surf_forecast_formatted = f"{match.group(1)}FT" if match else 'N/A'
        logging.info(f"Formatted surf forecast: {surf_forecast_formatted}")

        surf_text = surf_forecast_formatted
        match = re.search(r'(\d+)(?:\+\d*)?FT$', surf_text)
        surf_height = int(match.group(1)) if match else 0

        # Extract water temperature
        water_temp = 'N/A'
        water_temp_elem = soup.select_one('.current-data-desc')
        if water_temp_elem:
            # Get the text content and extract the temperature (e.g., "64°")
            temp_text = water_temp_elem.get_text(strip=True)
            temp_match = re.search(r'(\d+)°', temp_text)
            if temp_match:
                water_temp = f"{temp_match.group(1)}°"
                logging.info(f"Water temperature: {water_temp}")

        return {
            'text': surf_text,
            'height': surf_height,
            'water_temp': water_temp
        }

    def fetch_wind(self):
        """Fetch wind data and return raw data structure"""
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
            return None

    def fetch_tidetimes(self):
        """Fetch tide times data and return raw data structure"""
        logging.info("Fetching tide times data")
        today_date = datetime.now().strftime('%Y%m%d')
        url = f"https://tidesandcurrents.noaa.gov/cgi-bin/stationtideinfo.cgi?Stationid=9410230&datum=MLLW&timezone=LST_LDT&units=english&clock=12hour&decimalPlaces=2&date={today_date}"
        response = requests.get(url)
        if response.status_code != 200:
            logging.warning("Failed to fetch tide times data")
            return None

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
            next_type = next_type.strip()
            return {
                'time': next_time_dt,
                'time_str': next_time_dt.strftime('%H:%M'),
                'type': next_type
            }
        else:
            return None

    def fetch_tide(self):
        """Fetch tide data and return raw data structure"""
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
        """Fetch sunrise/sunset data and return raw data structure"""
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

        return {
            'event': next_event,
            'time': next_event_time,
            'sunrise': next_sunrise,
            'sunset': next_sunset
        }

    def fetch_current_time(self):
        return datetime.now().strftime('%H:%M:%S')

    def get_wireless_ssid(self):
        """Get the wireless SSID in a platform-agnostic way"""
        try:
            system = platform.system()
            if system == "Windows":
                # Windows: use netsh command
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'SSID' in line and 'BSSID' not in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                ssid = parts[1].strip()
                                if ssid and ssid != "":
                                    return ssid
            elif system == "Linux":
                # Linux: try iwgetid first, then fallback to nmcli
                try:
                    result = subprocess.run(
                        ['iwgetid', '-r'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except FileNotFoundError:
                    pass

                # Fallback to nmcli
                try:
                    result = subprocess.run(
                        ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.startswith('yes:'):
                                ssid = line.split(':')[1].strip()
                                if ssid:
                                    return ssid
                except FileNotFoundError:
                    pass
        except Exception as e:
            logging.warning(f"Error getting SSID: {e}")
        return "N/A"

    def get_ip_address(self):
        """Get the host IP address in a platform-agnostic way"""
        try:
            # Get all network interfaces
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                # Skip loopback interfaces
                if interface_name.startswith('lo') or interface_name.startswith('Loopback'):
                    continue
                for addr in addresses:
                    # Look for IPv4 addresses that are not loopback
                    # Use socket.AF_INET instead of psutil.AF_INET
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            return ip
        except Exception as e:
            logging.warning(f"Error getting IP address: {e}")
        return "N/A"

    def update_all_data(self):
        """Fetch all data sources and store in DataStore"""
        try:
            self.data_store['launches'] = self.fetch_launches()
        except Exception as e:
            logging.error(f"Error fetching launches: {e}", exc_info=True)
            self.data_store['launches'] = []

        try:
            self.data_store['surf'] = self.fetch_surf()
        except Exception as e:
            logging.error(f"Error fetching surf: {e}", exc_info=True)
            self.data_store['surf'] = None

        try:
            self.data_store['wind'] = self.fetch_wind()
        except Exception as e:
            logging.error(f"Error fetching wind: {e}", exc_info=True)
            self.data_store['wind'] = None

        try:
            self.data_store['tide'] = self.fetch_tide()
        except Exception as e:
            logging.error(f"Error fetching tide: {e}", exc_info=True)
            self.data_store['tide'] = None

        try:
            self.data_store['tide_times'] = self.fetch_tidetimes()
        except Exception as e:
            logging.error(f"Error fetching tide times: {e}", exc_info=True)
            self.data_store['tide_times'] = None

        try:
            self.data_store['sunriseset'] = self.fetch_sunriseset()
        except Exception as e:
            logging.error(f"Error fetching sunrise/sunset: {e}", exc_info=True)
            self.data_store['sunriseset'] = None

        try:
            import fetch_nws
            self.data_store['nws'] = fetch_nws.fetch_nws('92109')
        except Exception as e:
            logging.error(f"Error fetching NWS data: {e}", exc_info=True)
            self.data_store['nws'] = None

        self.data_store['last_update'] = datetime.now()
        self.last_update_time = datetime.now()

    def render_launch_cell(self, data_store):
        """Render launch cell using data from DataStore"""
        launches = data_store.get('launches', [])
        sunriseset = data_store.get('sunriseset')

        if not launches:
            return "None", None

        next_launch = launches[0]
        tz = pytz.timezone('America/Los_Angeles')
        days = next_launch['time_diff_days']
        hours = next_launch['time_diff_hours']

        launch_text = f"{next_launch['name']}\n{next_launch['time_diff']}"

        # Check if launch is within N minutes of sunrise or sunset
        sunrise_sunset_margin = 60
        color = None
        if days == 0 and hours < 12:
            local_time = next_launch['net'].astimezone(tz).strftime("%H:%M")
            launch_text = f"{next_launch['name']}\n{local_time}"

            if sunriseset:
                launch_time = next_launch['net']
                sunrise_time = sunriseset['sunrise']
                sunset_time = sunriseset['sunset']

                # Check if within 2 hours of sunrise or sunset
                time_diff_sunrise = abs((launch_time - sunrise_time).total_seconds())
                time_diff_sunset = abs((launch_time - sunset_time).total_seconds())

                if time_diff_sunrise <= (sunrise_sunset_margin * 60) or time_diff_sunset <= (sunrise_sunset_margin * 60):
                    color = self._color_orange
                else:
                    color = self._color_green
            else:
                color = self._color_green
        elif days == 0 and hours < 20:
            color = self._color_green

        return launch_text, color

    def render_surf_cell(self, data_store):
        """Render surf cell using data from DataStore"""
        surf = data_store.get('surf')

        if not surf:
            return "N/A", None

        surf_text = surf['text']
        surf_height = surf['height']
        water_temp = surf.get('water_temp', 'N/A')

        # Combine surf text with water temperature
        display_text = f"{surf_text}\n{water_temp}"

        if surf_height >= 5:
            return display_text, self._color_red
        elif surf_height >= 3:
            return display_text, self._color_green
        else:
            return display_text, None

    def render_wind_cell(self, data_store):
        """Render wind cell using data from DataStore"""
        wind = data_store.get('wind')

        if not wind:
            return "N/A", None

        wind_text = f"{wind['speed']}g{wind['gust']} {wind['direction']}"

        # Check for precipitation chance - light blue overrides green
        nws = data_store.get('nws')
        if nws and nws.get('precip_48h', 0) > 20:
            return wind_text, self._color_light_blue

        # Original wind-based color logic
        if wind['speed'] >= 11:
            return wind_text, self._color_green
        else:
            return wind_text, None

    def render_tide_cell(self, data_store):
        """Render tide cell using data from DataStore"""
        tide = data_store.get('tide')
        tide_times = data_store.get('tide_times')

        if not tide:
            return "N/A", None

        tide_value = tide['value']
        tide_trend = tide['trend']

        if isinstance(tide_value, (int, float)):
            tide_text = f"{tide_value:.1f}Ft {'v' if tide_trend == 'falling' else '^'}"
        else:
            tide_text = f"{tide_value}Ft {'v' if tide_trend == 'falling' else '^'}"

        if tide_times:
            tide_text += f"\n{tide_times['type'].capitalize()}@{tide_times['time_str']}"
        else:
            tide_text += "\nNo upcoming tide events"

        return tide_text, None

    def render_sunriseset_cell(self, data_store):
        """Render sunrise/sunset cell using data from DataStore"""
        sunriseset = data_store.get('sunriseset')

        if not sunriseset:
            return "N/A", None

        event_symbol = '^' if sunriseset['event'] == 'sunrise' else 'v'
        sun_time = sunriseset['time'].strftime('%H:%M')
        sun_text = f"{sun_time} {event_symbol}"

        return sun_text, None

    def update_all_cells(self):
        """Update all cells using render functions"""
        # Don't update cells if overlay is visible
        if self.overlay_visible:
            return

        grid_layout = self.layout()

        try:
            text, color = self.render_launch_cell(self.data_store)
            self.update_cell(grid_layout, (0, 0), "Launches", text, color)
        except Exception as e:
            logging.error(f"Error rendering launch cell: {e}", exc_info=True)
            self.update_cell(grid_layout, (0, 0), "Launches", "Error", None)

        try:
            text, color = self.render_surf_cell(self.data_store)
            self.update_cell(grid_layout, (0, 2), "Surf", text, color)
        except Exception as e:
            logging.error(f"Error rendering surf cell: {e}", exc_info=True)
            self.update_cell(grid_layout, (0, 2), "Surf", "Error", None)

        try:
            text, color = self.render_wind_cell(self.data_store)
            self.update_cell(grid_layout, (1, 1), "Wind", text, color)
        except Exception as e:
            logging.error(f"Error rendering wind cell: {e}", exc_info=True)
            self.update_cell(grid_layout, (1, 1), "Wind", "Error", None)

        try:
            text, color = self.render_tide_cell(self.data_store)
            self.update_cell(grid_layout, (1, 0), "Tides", text, color)
        except Exception as e:
            logging.error(f"Error rendering tide cell: {e}", exc_info=True)
            self.update_cell(grid_layout, (1, 0), "Tides", "Error", None)

        try:
            text, color = self.render_sunriseset_cell(self.data_store)
            self.update_cell(grid_layout, (0, 1), "Sunrise/Set", text, color)
        except Exception as e:
            logging.error(f"Error rendering sunrise/set cell: {e}", exc_info=True)
            self.update_cell(grid_layout, (0, 1), "Sunrise/Set", "Error", None)

    def update_data(self):
        """Fetch all data and update all cells"""
        self.update_all_data()  # Fetch all data into DataStore
        self.update_all_cells()  # Update all cells using DataStore

    def show_overlay(self):
        """Show the overlay dialog with additional details"""
        if self.overlay is None:
            self.create_overlay()
        else:
            # Refresh SSID and IP address each time overlay is shown
            ssid = self.get_wireless_ssid()
            ip_address = self.get_ip_address()
            # Find and update the SSID and IP labels
            for widget in self.overlay.findChildren(QLabel):
                if widget.text().startswith("SSID:"):
                    widget.setText(f"SSID: {ssid}")
                elif widget.text().startswith("IP Address:"):
                    widget.setText(f"IP Address: {ip_address}")
        self.overlay_visible = True
        self.overlay.raise_()
        self.overlay.show()

    def hide_overlay(self):
        """Hide the overlay dialog"""
        if self.overlay:
            self.overlay_visible = False
            self.overlay.hide()

    def create_overlay(self):
        """Create the overlay widget"""
        self.overlay = QWidget(self)
        self.overlay.setGeometry(0, 0, self._ui_width, self._ui_height)

        # Semi-transparent background
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")

        # Create content box (white box that wraps both text and X button)
        content_box = QWidget(self.overlay)
        content_box.setStyleSheet("background-color: white; border: 2px solid black;")
        content_box_width = int(self._ui_width * 0.8)
        content_box_height = int(self._ui_height * 0.6)
        content_box_x = (self._ui_width - content_box_width) // 2
        content_box_y = (self._ui_height - content_box_height) // 2
        content_box.setGeometry(content_box_x, content_box_y, content_box_width, content_box_height)

        # Create "Additional Details" label (no box around just the text)
        details_label = QLabel("Additional Details", content_box)
        details_label.setAlignment(Qt.AlignCenter)
        font = details_label.font()
        font.setBold(True)
        font.setPointSize(int(font.pointSize() * 1.5))
        details_label.setFont(font)
        details_label.setStyleSheet("background-color: transparent; border: none;")
        details_label.setGeometry(10, 10, content_box_width - 50, 40)

        # Get SSID and IP address
        ssid = self.get_wireless_ssid()
        ip_address = self.get_ip_address()

        # Create SSID label
        ssid_label = QLabel(f"SSID: {ssid}", content_box)
        ssid_label.setAlignment(Qt.AlignLeft)
        ssid_font = ssid_label.font()
        ssid_font.setPointSize(int(ssid_font.pointSize() * 1.2))
        ssid_label.setFont(ssid_font)
        ssid_label.setStyleSheet("background-color: transparent; border: none;")
        ssid_label.setGeometry(20, 60, content_box_width - 40, 30)

        # Create IP address label
        ip_label = QLabel(f"IP Address: {ip_address}", content_box)
        ip_label.setAlignment(Qt.AlignLeft)
        ip_font = ip_label.font()
        ip_font.setPointSize(int(ip_font.pointSize() * 1.2))
        ip_label.setFont(ip_font)
        ip_label.setStyleSheet("background-color: transparent; border: none;")
        ip_label.setGeometry(20, 100, content_box_width - 40, 30)

        # Create close button (X) in upper right corner of content box
        close_button = QPushButton("×", content_box)
        close_button.setStyleSheet("background-color: #ff4444; color: white; border: 1px solid black; font-size: 20px; font-weight: bold;")
        close_button.setGeometry(content_box_width - 40, 5, 35, 35)
        close_button.clicked.connect(self.hide_overlay)

        self.overlay.hide()

    def update_time_cell(self):
        # Don't update clock cell if overlay is visible
        if self.overlay_visible:
            return

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
            self.update_cell(grid_layout, (1, 2), 'Clock', clock_text, clickable=True, click_callback=self.show_overlay)

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

