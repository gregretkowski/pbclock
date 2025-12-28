import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import MainWindow


class TestMainWindow(unittest.TestCase):
    """Test suite for MainWindow class"""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication once for all tests"""
        cls.app = QApplication([])

    @classmethod
    def tearDownClass(cls):
        """Clean up QApplication"""
        cls.app.quit()

    def setUp(self):
        """Set up test fixtures"""
        self.window = MainWindow()

    def test_data_store_initialization(self):
        """Test that DataStore is properly initialized"""
        self.assertIsNotNone(self.window.data_store)
        self.assertEqual(self.window.data_store['launches'], [])
        self.assertIsNone(self.window.data_store['surf'])
        self.assertIsNone(self.window.data_store['wind'])
        self.assertIsNone(self.window.data_store['tide'])
        self.assertIsNone(self.window.data_store['tide_times'])
        self.assertIsNone(self.window.data_store['sunriseset'])

    @patch('main.requests.get')
    @patch('main.dateparser.parse')
    def test_fetch_launches(self, mock_parse, mock_get):
        """Test fetch_launches function"""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'name': 'Test Launch 1',
                'location': 'Vandenberg Space Force Base',
                'net': '2024-12-20T10:00:00Z'
            },
            {
                'name': 'Test Launch 2',
                'location': 'Chica Launch Site',
                'net': '2024-12-21T15:00:00Z'
            },
            {
                'name': 'Test Launch 3',
                'location': 'Somewhere Else',
                'net': '2024-12-22T20:00:00Z'
            }
        ]
        mock_get.return_value = mock_response

        # Mock dateparser to return timezone-aware datetime
        tz = pytz.timezone('America/Los_Angeles')
        future_time = datetime.now(tz) + timedelta(days=2, hours=5)
        mock_parse.return_value = future_time

        # Call the function
        result = self.window.fetch_launches()

        # Assertions
        self.assertEqual(len(result), 2)  # Only Vandenberg and Chica
        self.assertEqual(result[0]['name'], 'Test Launch 1')
        self.assertIn('net', result[0])
        self.assertIn('time_diff', result[0])
        self.assertIn('time_diff_days', result[0])
        self.assertIn('time_diff_hours', result[0])

    @patch('main.requests.get')
    @patch('main.BeautifulSoup')
    def test_fetch_surf(self, mock_bs, mock_get):
        """Test fetch_surf function"""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response

        # Mock BeautifulSoup
        mock_soup = Mock()
        mock_element = Mock()
        mock_element.text = 'Pacific Beach 3-5FT'
        mock_soup.select_one.return_value = mock_element
        mock_bs.return_value = mock_soup

        # Call the function
        result = self.window.fetch_surf()

        # Assertions
        self.assertIsNotNone(result)
        self.assertIn('text', result)
        self.assertIn('height', result)
        # The regex r'(\d+)(?:\+\d*)?FT$' matches "5FT" from "3-5FT", extracting 5
        self.assertEqual(result['height'], 5)

    @patch('main.requests.get')
    def test_fetch_wind(self, mock_get):
        """Test fetch_wind function"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'observations': [{
                'imperial': {
                    'windSpeed': 15,
                    'windGust': 20
                },
                'winddir': 180  # South
            }]
        }
        mock_get.return_value = mock_response

        # Call the function
        result = self.window.fetch_wind()

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['speed'], 15)
        self.assertEqual(result['gust'], 20)
        self.assertEqual(result['direction'], 'S')

    @patch('main.requests.get')
    def test_fetch_wind_no_data(self, mock_get):
        """Test fetch_wind when no observations available"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = self.window.fetch_wind()
        self.assertIsNone(result)

    @patch('main.requests.get')
    def test_fetch_tide(self, mock_get):
        """Test fetch_tide function"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {'v': '2.5', 't': '2024-12-20 10:00:00'},
                {'v': '3.0', 't': '2024-12-20 11:00:00'}
            ]
        }
        mock_get.return_value = mock_response

        # Call the function
        result = self.window.fetch_tide()

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], 3.0)
        self.assertEqual(result['trend'], 'rising')

    @patch('main.requests.get')
    def test_fetch_tidetimes(self, mock_get):
        """Test fetch_tidetimes function"""
        # Mock response with tide data
        current_time = datetime.now()
        future_time = current_time + timedelta(hours=2)
        time_str = future_time.strftime('%I:%M %p')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"{time_str}|3.5|High Tide"
        mock_get.return_value = mock_response

        # Call the function
        result = self.window.fetch_tidetimes()

        # Assertions
        self.assertIsNotNone(result)
        self.assertIn('time', result)
        self.assertIn('time_str', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'].strip(), 'High Tide')

    @patch('main.sun')
    def test_fetch_sunriseset(self, mock_sun):
        """Test fetch_sunriseset function"""
        tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(tz)
        sunrise_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
        sunset_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)

        # Mock sun function
        mock_sun.return_value = {
            'sunrise': sunrise_time,
            'sunset': sunset_time
        }

        # Call the function
        result = self.window.fetch_sunriseset()

        # Assertions
        self.assertIsNotNone(result)
        self.assertIn('event', result)
        self.assertIn('time', result)
        self.assertIn('sunrise', result)
        self.assertIn('sunset', result)

    def test_render_launch_cell_no_launches(self):
        """Test render_launch_cell with no launches"""
        data_store = {'launches': []}
        text, color = self.window.render_launch_cell(data_store)
        self.assertEqual(text, "None")
        self.assertIsNone(color)

    def test_render_launch_cell_with_launch(self):
        """Test render_launch_cell with launch data"""
        tz = pytz.timezone('America/Los_Angeles')
        launch_time = datetime.now(tz) + timedelta(hours=10)

        data_store = {
            'launches': [{
                'name': 'Test Launch',
                'net': launch_time,
                'time_diff': '0D 10H',
                'time_diff_days': 0,
                'time_diff_hours': 10
            }],
            'sunriseset': None
        }

        text, color = self.window.render_launch_cell(data_store)
        self.assertIn('Test Launch', text)
        self.assertEqual(color, self.window._color_green)

    def test_render_launch_cell_near_sunrise(self):
        """Test render_launch_cell when launch is near sunrise"""
        tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(tz)
        launch_time = current_time + timedelta(hours=2)
        sunrise_time = current_time + timedelta(hours=2, minutes=30)  # 30 min after launch

        data_store = {
            'launches': [{
                'name': 'Test Launch',
                'net': launch_time,
                'time_diff': '0D 2H',
                'time_diff_days': 0,
                'time_diff_hours': 2
            }],
            'sunriseset': {
                'sunrise': sunrise_time,
                'sunset': current_time + timedelta(hours=12),
                'event': 'sunrise',
                'time': sunrise_time
            }
        }

        text, color = self.window.render_launch_cell(data_store)
        # Should be orange because within 1 hour of sunrise
        self.assertEqual(color, self.window._color_orange)

    def test_render_launch_cell_near_sunset(self):
        """Test render_launch_cell when launch is near sunset"""
        tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(tz)
        launch_time = current_time + timedelta(hours=2)
        sunset_time = current_time + timedelta(hours=2, minutes=30)  # 30 min after launch

        data_store = {
            'launches': [{
                'name': 'Test Launch',
                'net': launch_time,
                'time_diff': '0D 2H',
                'time_diff_days': 0,
                'time_diff_hours': 2
            }],
            'sunriseset': {
                'sunrise': current_time + timedelta(hours=12),
                'sunset': sunset_time,
                'event': 'sunset',
                'time': sunset_time
            }
        }

        text, color = self.window.render_launch_cell(data_store)
        # Should be orange because within 1 hour of sunset
        self.assertEqual(color, self.window._color_orange)

    def test_render_launch_cell_far_from_sunrise_sunset(self):
        """Test render_launch_cell when launch is far from sunrise/sunset"""
        tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(tz)
        launch_time = current_time + timedelta(hours=2)
        sunrise_time = current_time + timedelta(hours=5)  # 3 hours after launch

        data_store = {
            'launches': [{
                'name': 'Test Launch',
                'net': launch_time,
                'time_diff': '0D 2H',
                'time_diff_days': 0,
                'time_diff_hours': 2
            }],
            'sunriseset': {
                'sunrise': sunrise_time,
                'sunset': current_time + timedelta(hours=12),
                'event': 'sunrise',
                'time': sunrise_time
            }
        }

        text, color = self.window.render_launch_cell(data_store)
        # Should be green because more than 1 hour from sunrise/sunset
        self.assertEqual(color, self.window._color_green)

    def test_render_launch_cell_before_sunrise(self):
        """Test render_launch_cell when launch is before sunrise (within 1 hour)"""
        tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(tz)
        sunrise_time = current_time + timedelta(hours=2)
        launch_time = current_time + timedelta(hours=1, minutes=30)  # 30 min before sunrise

        data_store = {
            'launches': [{
                'name': 'Test Launch',
                'net': launch_time,
                'time_diff': '0D 1H',
                'time_diff_days': 0,
                'time_diff_hours': 1
            }],
            'sunriseset': {
                'sunrise': sunrise_time,
                'sunset': current_time + timedelta(hours=12),
                'event': 'sunrise',
                'time': sunrise_time
            }
        }

        text, color = self.window.render_launch_cell(data_store)
        # Should be orange because within 1 hour of sunrise (30 min difference)
        self.assertEqual(color, self.window._color_orange)

    def test_render_surf_cell_high(self):
        """Test render_surf_cell with high surf"""
        data_store = {
            'surf': {
                'text': '5FT',
                'height': 5
            }
        }
        text, color = self.window.render_surf_cell(data_store)
        self.assertEqual(text, '5FT')
        self.assertEqual(color, self.window._color_red)

    def test_render_surf_cell_medium(self):
        """Test render_surf_cell with medium surf"""
        data_store = {
            'surf': {
                'text': '3FT',
                'height': 3
            }
        }
        text, color = self.window.render_surf_cell(data_store)
        self.assertEqual(text, '3FT')
        self.assertEqual(color, self.window._color_green)

    def test_render_surf_cell_low(self):
        """Test render_surf_cell with low surf"""
        data_store = {
            'surf': {
                'text': '2FT',
                'height': 2
            }
        }
        text, color = self.window.render_surf_cell(data_store)
        self.assertEqual(text, '2FT')
        self.assertIsNone(color)

    def test_render_wind_cell_high(self):
        """Test render_wind_cell with high wind"""
        data_store = {
            'wind': {
                'speed': 15,
                'gust': 20,
                'direction': 'SW'
            }
        }
        text, color = self.window.render_wind_cell(data_store)
        self.assertIn('15', text)
        self.assertIn('20', text)
        self.assertIn('SW', text)
        self.assertEqual(color, self.window._color_green)

    def test_render_wind_cell_low(self):
        """Test render_wind_cell with low wind"""
        data_store = {
            'wind': {
                'speed': 5,
                'gust': 8,
                'direction': 'N'
            }
        }
        text, color = self.window.render_wind_cell(data_store)
        self.assertIsNone(color)

    def test_render_tide_cell(self):
        """Test render_tide_cell"""
        data_store = {
            'tide': {
                'value': 3.5,
                'trend': 'rising'
            },
            'tide_times': {
                'time_str': '10:30',
                'type': 'High Tide'
            }
        }
        text, color = self.window.render_tide_cell(data_store)
        self.assertIn('3.5', text)
        self.assertIn('^', text)  # Rising
        # capitalize() only capitalizes first letter, rest lowercase
        self.assertIn('High tide', text)
        self.assertIn('10:30', text)

    def test_render_sunriseset_cell(self):
        """Test render_sunriseset_cell"""
        tz = pytz.timezone('America/Los_Angeles')
        sunrise_time = datetime.now(tz).replace(hour=6, minute=30)

        data_store = {
            'sunriseset': {
                'event': 'sunrise',
                'time': sunrise_time,
                'sunrise': sunrise_time,
                'sunset': datetime.now(tz).replace(hour=18, minute=0)
            }
        }
        text, color = self.window.render_sunriseset_cell(data_store)
        self.assertIn('06:30', text)
        self.assertIn('^', text)  # Sunrise symbol

    @patch.object(MainWindow, 'fetch_launches')
    @patch.object(MainWindow, 'fetch_surf')
    @patch.object(MainWindow, 'fetch_wind')
    @patch.object(MainWindow, 'fetch_tide')
    @patch.object(MainWindow, 'fetch_tidetimes')
    @patch.object(MainWindow, 'fetch_sunriseset')
    def test_update_all_data(self, mock_sunriseset, mock_tidetimes, mock_tide,
                             mock_wind, mock_surf, mock_launches):
        """Test update_all_data method"""
        # Set up mocks
        mock_launches.return_value = [{'name': 'Test Launch'}]
        mock_surf.return_value = {'text': '3FT', 'height': 3}
        mock_wind.return_value = {'speed': 10, 'gust': 15, 'direction': 'SW'}
        mock_tide.return_value = {'value': 2.5, 'trend': 'rising'}
        mock_tidetimes.return_value = {'time_str': '10:00', 'type': 'High'}
        mock_sunriseset.return_value = {
            'event': 'sunrise',
            'time': datetime.now(),
            'sunrise': datetime.now(),
            'sunset': datetime.now()
        }

        # Call the function
        self.window.update_all_data()

        # Assertions
        self.assertEqual(len(self.window.data_store['launches']), 1)
        self.assertIsNotNone(self.window.data_store['surf'])
        self.assertIsNotNone(self.window.data_store['wind'])
        self.assertIsNotNone(self.window.data_store['tide'])
        self.assertIsNotNone(self.window.data_store['tide_times'])
        self.assertIsNotNone(self.window.data_store['sunriseset'])
        self.assertIsNotNone(self.window.data_store['last_update'])

    @patch.object(MainWindow, 'update_cell')
    def test_update_all_cells(self, mock_update_cell):
        """Test update_all_cells method"""
        # Set up data store
        tz = pytz.timezone('America/Los_Angeles')
        self.window.data_store = {
            'launches': [{
                'name': 'Test Launch',
                'net': datetime.now(tz) + timedelta(hours=5),
                'time_diff': '0D 5H',
                'time_diff_days': 0,
                'time_diff_hours': 5
            }],
            'surf': {'text': '3FT', 'height': 3},
            'wind': {'speed': 10, 'gust': 15, 'direction': 'SW'},
            'tide': {'value': 2.5, 'trend': 'rising'},
            'tide_times': {'time_str': '10:00', 'type': 'High'},
            'sunriseset': {
                'event': 'sunrise',
                'time': datetime.now(tz),
                'sunrise': datetime.now(tz),
                'sunset': datetime.now(tz)
            }
        }

        # Call the function
        self.window.update_all_cells()

        # Assertions - should call update_cell for each cell
        self.assertGreaterEqual(mock_update_cell.call_count, 5)

    @patch.object(MainWindow, 'update_all_data')
    @patch.object(MainWindow, 'update_all_cells')
    def test_update_data(self, mock_update_cells, mock_update_data):
        """Test update_data method calls both fetch and display"""
        self.window.update_data()
        mock_update_data.assert_called_once()
        mock_update_cells.assert_called_once()

    @patch.object(MainWindow, 'fetch_launches')
    def test_update_all_data_error_handling(self, mock_launches):
        """Test that update_all_data handles errors gracefully"""
        # Make fetch_launches raise an exception
        mock_launches.side_effect = Exception("Network error")

        # Should not raise, but store empty list
        self.window.update_all_data()
        self.assertEqual(self.window.data_store['launches'], [])


if __name__ == '__main__':
    unittest.main()

