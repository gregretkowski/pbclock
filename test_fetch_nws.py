import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
import pytz

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_nws


class TestFetchNWS(unittest.TestCase):
    """Test suite for fetch_nws module"""

    @patch('fetch_nws.requests.get')
    def test_get_lat_lon_from_zip_known_zip(self, mock_get):
        """Test get_lat_lon_from_zip with known ZIP code"""
        lat, lon = fetch_nws.get_lat_lon_from_zip('92109')
        self.assertEqual(lat, 32.7934)
        self.assertEqual(lon, -117.2544)
        # Should not make HTTP call for known ZIP
        mock_get.assert_not_called()

    @patch('fetch_nws.requests.get')
    def test_get_lat_lon_from_zip_census_api(self, mock_get):
        """Test get_lat_lon_from_zip using Census geocoding API"""
        # Mock Census API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': {
                'addressMatches': [{
                    'coordinates': {
                        'y': 40.7128,
                        'x': -74.0060
                    }
                }]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        lat, lon = fetch_nws.get_lat_lon_from_zip('10001')
        self.assertEqual(lat, 40.7128)
        self.assertEqual(lon, -74.0060)
        mock_get.assert_called_once()

    @patch('fetch_nws.requests.get')
    def test_get_lat_lon_from_zip_nominatim_fallback(self, mock_get):
        """Test get_lat_lon_from_zip using Nominatim fallback"""
        # First call (Census) fails, second call (Nominatim) succeeds
        mock_census_response = Mock()
        mock_census_response.raise_for_status.side_effect = Exception("API Error")

        mock_nominatim_response = Mock()
        mock_nominatim_response.json.return_value = [{
            'lat': '40.7128',
            'lon': '-74.0060'
        }]
        mock_nominatim_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_census_response, mock_nominatim_response]

        lat, lon = fetch_nws.get_lat_lon_from_zip('10001')
        self.assertEqual(lat, 40.7128)
        self.assertEqual(lon, -74.0060)
        self.assertEqual(mock_get.call_count, 2)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_success(self, mock_get, mock_geocode):
        """Test fetch_nws with successful API calls"""
        # Mock geocoding
        mock_geocode.return_value = (32.7934, -117.2544)

        # Mock NWS point API response
        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/SGX/33,70/forecast'
            }
        }
        mock_point_response.raise_for_status = Mock()

        # Mock NWS forecast API response
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Create periods that are in the future
        today_daytime = (now + timedelta(hours=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        today_night = (now + timedelta(hours=10)).replace(hour=20, minute=0, second=0, microsecond=0)
        tomorrow_daytime = (now + timedelta(days=1, hours=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        tomorrow_night = (now + timedelta(days=1, hours=10)).replace(hour=20, minute=0, second=0, microsecond=0)

        mock_forecast_response = Mock()
        mock_forecast_response.json.return_value = {
            'properties': {
                'periods': [
                    {
                        'name': 'Today',
                        'startTime': today_daytime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': True,
                        'temperature': 68,
                        'cloudCover': 30,  # Numeric value (30%)
                        'probabilityOfPrecipitation': {'value': 10}
                    },
                    {
                        'name': 'Tonight',
                        'startTime': today_night.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': False,
                        'temperature': 57,
                        'cloudCover': 0,  # Clear (0%)
                        'probabilityOfPrecipitation': {'value': 5}
                    },
                    {
                        'name': 'Tomorrow',
                        'startTime': tomorrow_daytime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': True,
                        'temperature': 72,
                        'cloudCover': 100,  # Overcast (100%)
                        'probabilityOfPrecipitation': {'value': 60}
                    },
                    {
                        'name': 'Tomorrow Night',
                        'startTime': tomorrow_night.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': False,
                        'temperature': 62,
                        'cloudCover': 75,  # Broken (75%)
                        'probabilityOfPrecipitation': {'value': 40}
                    }
                ]
            }
        }
        mock_forecast_response.raise_for_status = Mock()

        # Configure mock_get to return different responses based on URL
        call_count = [0]
        def get_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is point API
                return mock_point_response
            elif call_count[0] == 2:  # Second call is forecast API
                return mock_forecast_response
            return Mock()

        mock_get.side_effect = get_side_effect

        # Call the function
        result = fetch_nws.fetch_nws('92109')

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['high'], 68)
        self.assertEqual(result['low'], 57)
        # Cloud cover should be from daytime period
        self.assertEqual(result['cloud_cover'], 30)
        self.assertEqual(result['precip_today'], 10)  # Max of today's periods
        self.assertEqual(result['precip_tomorrow'], 60)  # Max of tomorrow's periods
        self.assertEqual(result['precip_48h'], 60)  # Max in next 48h

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_with_numeric_cloud_cover(self, mock_get, mock_geocode):
        """Test fetch_nws with numeric cloud cover values"""
        # Mock geocoding
        mock_geocode.return_value = (32.7934, -117.2544)

        # Mock NWS point API response
        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/SGX/33,70/forecast'
            }
        }
        mock_point_response.raise_for_status = Mock()

        # Mock NWS forecast API response with numeric cloud cover
        now = datetime.now()
        today = now.date()

        # Create periods that are in the future
        today_daytime = (now + timedelta(hours=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        today_night = (now + timedelta(hours=10)).replace(hour=20, minute=0, second=0, microsecond=0)

        mock_forecast_response = Mock()
        mock_forecast_response.json.return_value = {
            'properties': {
                'periods': [
                    {
                        'name': 'Today',
                        'startTime': today_daytime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': True,
                        'temperature': 70,
                        'cloudCover': 25,  # Numeric value
                        'probabilityOfPrecipitation': {'value': 15}
                    },
                    {
                        'name': 'Tonight',
                        'startTime': today_night.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': False,
                        'temperature': 58,
                        'cloudCover': 10,
                        'probabilityOfPrecipitation': {'value': 5}
                    }
                ]
            }
        }
        mock_forecast_response.raise_for_status = Mock()

        call_count = [0]
        def get_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is point API
                return mock_point_response
            elif call_count[0] == 2:  # Second call is forecast API
                return mock_forecast_response
            return Mock()

        mock_get.side_effect = get_side_effect

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNotNone(result)
        self.assertEqual(result['high'], 70)
        self.assertEqual(result['low'], 58)
        self.assertEqual(result['cloud_cover'], 25)  # From daytime period
        self.assertEqual(result['precip_today'], 15)

    @patch('fetch_nws.get_lat_lon_from_zip')
    def test_fetch_nws_geocoding_failure(self, mock_geocode):
        """Test fetch_nws when geocoding fails"""
        mock_geocode.return_value = (None, None)

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNone(result)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_point_api_failure(self, mock_get, mock_geocode):
        """Test fetch_nws when NWS point API fails"""
        mock_geocode.return_value = (32.7934, -117.2544)

        mock_point_response = Mock()
        mock_point_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_point_response

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNone(result)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_forecast_api_failure(self, mock_get, mock_geocode):
        """Test fetch_nws when NWS forecast API fails"""
        mock_geocode.return_value = (32.7934, -117.2544)

        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/SGX/33,70/forecast'
            }
        }
        mock_point_response.raise_for_status = Mock()

        mock_forecast_response = Mock()
        mock_forecast_response.raise_for_status.side_effect = Exception("API Error")

        call_count = [0]
        def get_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is point API
                return mock_point_response
            elif call_count[0] == 2:  # Second call is forecast API
                return mock_forecast_response
            return Mock()

        mock_get.side_effect = get_side_effect

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNone(result)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_missing_forecast_url(self, mock_get, mock_geocode):
        """Test fetch_nws when point API doesn't return forecast URL"""
        mock_geocode.return_value = (32.7934, -117.2544)

        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {}  # Missing forecast URL
        }
        mock_point_response.raise_for_status = Mock()
        mock_get.return_value = mock_point_response

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNone(result)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_no_periods(self, mock_get, mock_geocode):
        """Test fetch_nws when forecast has no periods"""
        mock_geocode.return_value = (32.7934, -117.2544)

        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/SGX/33,70/forecast'
            }
        }
        mock_point_response.raise_for_status = Mock()

        mock_forecast_response = Mock()
        mock_forecast_response.json.return_value = {
            'properties': {}  # Missing periods
        }
        mock_forecast_response.raise_for_status = Mock()

        call_count = [0]
        def get_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is point API
                return mock_point_response
            elif call_count[0] == 2:  # Second call is forecast API
                return mock_forecast_response
            return Mock()

        mock_get.side_effect = get_side_effect

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNone(result)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_default_precip_values(self, mock_get, mock_geocode):
        """Test fetch_nws when precipitation values are None (should default to 0)"""
        mock_geocode.return_value = (32.7934, -117.2544)

        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/SGX/33,70/forecast'
            }
        }
        mock_point_response.raise_for_status = Mock()

        now = datetime.now()
        today = now.date()

        # Create periods that are in the future
        today_daytime = (now + timedelta(hours=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        today_night = (now + timedelta(hours=10)).replace(hour=20, minute=0, second=0, microsecond=0)

        mock_forecast_response = Mock()
        mock_forecast_response.json.return_value = {
            'properties': {
                'periods': [
                    {
                        'name': 'Today',
                        'startTime': today_daytime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': True,
                        'temperature': 70,
                        'cloudCover': 0,
                        'probabilityOfPrecipitation': {'value': None}  # None value
                    },
                    {
                        'name': 'Tonight',
                        'startTime': today_night.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'isDaytime': False,
                        'temperature': 58,
                        'cloudCover': 0,
                        # Missing probabilityOfPrecipitation
                    }
                ]
            }
        }
        mock_forecast_response.raise_for_status = Mock()

        call_count = [0]
        def get_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is point API
                return mock_point_response
            elif call_count[0] == 2:  # Second call is forecast API
                return mock_forecast_response
            return Mock()

        mock_get.side_effect = get_side_effect

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNotNone(result)
        self.assertEqual(result['precip_today'], 0)  # Should default to 0
        self.assertEqual(result['precip_tomorrow'], 0)
        self.assertEqual(result['precip_48h'], 0)
        self.assertEqual(result['cloud_cover'], 0)

    @patch('fetch_nws.get_lat_lon_from_zip')
    @patch('fetch_nws.requests.get')
    def test_fetch_nws_48h_precipitation(self, mock_get, mock_geocode):
        """Test fetch_nws correctly finds max precipitation in 48 hours"""
        mock_geocode.return_value = (32.7934, -117.2544)

        mock_point_response = Mock()
        mock_point_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/SGX/33,70/forecast'
            }
        }
        mock_point_response.raise_for_status = Mock()

        # Use UTC timezone to match NWS API format
        utc = pytz.UTC
        now = datetime.now(utc)
        today = now.date()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)

        # Create periods spanning 48+ hours with proper datetime formatting
        periods = []
        # Today (2 hours ahead)
        today_start = (now + timedelta(hours=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        periods.append({
            'name': 'Today',
            'startTime': today_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'isDaytime': True,
            'temperature': 70,
            'cloudCover': 0,
            'probabilityOfPrecipitation': {'value': 20}
        })
        # Tonight (10 hours ahead)
        tonight_start = (now + timedelta(hours=10)).replace(hour=20, minute=0, second=0, microsecond=0)
        periods.append({
            'name': 'Tonight',
            'startTime': tonight_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'isDaytime': False,
            'temperature': 58,
            'cloudCover': 0,
            'probabilityOfPrecipitation': {'value': 30}
        })
        # Tomorrow (24 hours ahead - within 48h)
        tomorrow_start = (now + timedelta(hours=24)).replace(hour=12, minute=0, second=0, microsecond=0)
        periods.append({
            'name': 'Tomorrow',
            'startTime': tomorrow_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'isDaytime': True,
            'temperature': 72,
            'cloudCover': 0,
            'probabilityOfPrecipitation': {'value': 80}  # Highest in 48h
        })
        # Tomorrow night (36 hours ahead - within 48h)
        tomorrow_night_start = (now + timedelta(hours=36)).replace(hour=20, minute=0, second=0, microsecond=0)
        periods.append({
            'name': 'Tomorrow Night',
            'startTime': tomorrow_night_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'isDaytime': False,
            'temperature': 60,
            'cloudCover': 0,
            'probabilityOfPrecipitation': {'value': 50}
        })
        # Day after (50 hours ahead - clearly outside 48h, should be excluded)
        # Using 50 hours to ensure it's well outside the 48-hour window
        day_after_start = now + timedelta(hours=50)
        periods.append({
            'name': 'Day After',
            'startTime': day_after_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'isDaytime': True,
            'temperature': 75,
            'cloudCover': 0,
            'probabilityOfPrecipitation': {'value': 90}  # Should not be included (outside 48h)
        })

        mock_forecast_response = Mock()
        mock_forecast_response.json.return_value = {
            'properties': {
                'periods': periods
            }
        }
        mock_forecast_response.raise_for_status = Mock()

        call_count = [0]
        def get_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is point API
                return mock_point_response
            elif call_count[0] == 2:  # Second call is forecast API
                return mock_forecast_response
            return Mock()

        mock_get.side_effect = get_side_effect

        result = fetch_nws.fetch_nws('92109')

        self.assertIsNotNone(result)
        # Should be max of periods within 48 hours (80), not 90
        # The period at 50 hours should be excluded
        self.assertLessEqual(result['precip_48h'], 80,
                            f"Expected precip_48h <= 80, got {result['precip_48h']}. "
                            f"The 50-hour period (90%) should be excluded from 48h calculation.")
        self.assertEqual(result['precip_48h'], 80)


if __name__ == '__main__':
    unittest.main()

