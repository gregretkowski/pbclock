import requests
import logging
from datetime import datetime, timedelta


def get_lat_lon_from_zip(zip_code):
    """Convert ZIP code to latitude and longitude using geocoding API with fallback"""
    # Known coordinates for common zip codes (can be expanded)
    known_zips = {
        '92109': (32.7934, -117.2544),  # Pacific Beach, San Diego
    }

    if zip_code in known_zips:
        lat, lon = known_zips[zip_code]
        logging.info(f"Using known coordinates for ZIP {zip_code}: lat={lat}, lon={lon}")
        return lat, lon

    # Try US Census geocoding API
    try:
        geocode_url = f"https://geocoding.geo.census.gov/geocoder/locations/address?zip={zip_code}&benchmark=Public_AR_Census2020&format=json"
        response = requests.get(geocode_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'result' in data and 'addressMatches' in data['result'] and len(data['result']['addressMatches']) > 0:
            coordinates = data['result']['addressMatches'][0]['coordinates']
            lat = coordinates['y']
            lon = coordinates['x']
            logging.info(f"Geocoded ZIP {zip_code} to lat={lat}, lon={lon}")
            return lat, lon
        else:
            logging.warning(f"No coordinates found for ZIP {zip_code}")
            return None, None
    except Exception as e:
        logging.warning(f"Error geocoding ZIP {zip_code} with Census API: {e}, trying alternative")

        # Fallback to Nominatim (OpenStreetMap) geocoding
        try:
            geocode_url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=US&format=json&limit=1"
            headers = {'User-Agent': 'pbclock/1.0 (weather app)'}
            response = requests.get(geocode_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logging.info(f"Geocoded ZIP {zip_code} via Nominatim to lat={lat}, lon={lon}")
                return lat, lon
            else:
                logging.warning(f"No coordinates found for ZIP {zip_code}")
                return None, None
        except Exception as e2:
            logging.error(f"Error geocoding ZIP {zip_code} with Nominatim: {e2}")
            return None, None


def fetch_nws(zip_code='92109'):
    """Fetch National Weather Service data and return raw data structure

    Args:
        zip_code: ZIP code to fetch weather for (default: 92109)

    Returns:
        Dictionary with:
            - high: High temperature for today (int)
            - low: Low temperature for today (int)
            - cloud_cover: Cloud cover percentage for today (int, 0-100)
            - precip_today: Precipitation chance for today (int, 0-100)
            - precip_tomorrow: Precipitation chance for tomorrow (int, 0-100)
            - precip_48h: Maximum precipitation chance in next 48 hours (int, 0-100)
    """
    logging.info(f"Fetching NWS data for ZIP {zip_code} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Convert ZIP to lat/lon
    lat, lon = get_lat_lon_from_zip(zip_code)
    if lat is None or lon is None:
        logging.warning("Failed to geocode ZIP code")
        return None

    try:
        # Get point information from NWS
        point_url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {
            'User-Agent': 'pbclock/1.0 (weather app)',
            'Accept': 'application/json'
        }
        point_response = requests.get(point_url, headers=headers, timeout=10)
        point_response.raise_for_status()
        point_data = point_response.json()

        if 'properties' not in point_data or 'forecast' not in point_data['properties']:
            logging.warning("No forecast URL in point data")
            return None

        # Get forecast
        forecast_url = point_data['properties']['forecast']
        forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        if 'properties' not in forecast_data or 'periods' not in forecast_data['properties']:
            logging.warning("No periods in forecast data")
            return None

        periods = forecast_data['properties']['periods']

        # Find today's periods (daytime and nighttime)
        current_date = datetime.now().date()
        today_periods = []
        tomorrow_periods = []
        next_48h_periods = []

        for period in periods:
            period_start = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
            period_date = period_start.date()

            # Check if period is within next 48 hours
            hours_ahead = (period_start - datetime.now(period_start.tzinfo)).total_seconds() / 3600
            if 0 <= hours_ahead <= 48:
                next_48h_periods.append(period)

            # Check if period is today
            if period_date == current_date:
                today_periods.append(period)
            # Check if period is tomorrow
            elif period_date == current_date + timedelta(days=1):
                tomorrow_periods.append(period)

        # Extract today's high/low
        today_high = None
        today_low = None
        today_cloud_cover = None
        today_precip = None

        for period in today_periods:
            temp = period.get('temperature')
            is_daytime = period.get('isDaytime', False)
            cloud_cover = period.get('cloudCover')
            precip = period.get('probabilityOfPrecipitation', {}).get('value')

            if is_daytime:
                if today_high is None or (temp is not None and temp > today_high):
                    today_high = temp
                if cloud_cover is not None:
                    today_cloud_cover = cloud_cover
                if precip is not None:
                    if today_precip is None or precip > today_precip:
                        today_precip = precip
            else:
                if today_low is None or (temp is not None and temp < today_low):
                    today_low = temp
                if cloud_cover is not None and today_cloud_cover is None:
                    today_cloud_cover = cloud_cover
                if precip is not None:
                    if today_precip is None or precip > today_precip:
                        today_precip = precip

        # If we don't have today's high/low yet, try to get from first periods
        if today_high is None or today_low is None:
            for period in periods[:4]:  # Check first few periods
                temp = period.get('temperature')
                is_daytime = period.get('isDaytime', False)
                period_start = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
                period_date = period_start.date()

                if period_date == current_date:
                    if is_daytime and today_high is None and temp is not None:
                        today_high = temp
                    elif not is_daytime and today_low is None and temp is not None:
                        today_low = temp

        # Get tomorrow's max precipitation chance
        tomorrow_precip = None
        for period in tomorrow_periods:
            precip = period.get('probabilityOfPrecipitation', {}).get('value')
            if precip is not None:
                if tomorrow_precip is None or precip > tomorrow_precip:
                    tomorrow_precip = precip

        # Get max precipitation in next 48 hours
        max_48h_precip = None
        for period in next_48h_periods:
            precip = period.get('probabilityOfPrecipitation', {}).get('value')
            if precip is not None:
                if max_48h_precip is None or precip > max_48h_precip:
                    max_48h_precip = precip

        # Default to 0 if None
        today_precip = today_precip if today_precip is not None else 0
        tomorrow_precip = tomorrow_precip if tomorrow_precip is not None else 0
        max_48h_precip = max_48h_precip if max_48h_precip is not None else 0
        today_cloud_cover = today_cloud_cover if today_cloud_cover is not None else 0

        result = {
            'high': today_high,
            'low': today_low,
            'cloud_cover': today_cloud_cover,
            'precip_today': today_precip,
            'precip_tomorrow': tomorrow_precip,
            'precip_48h': max_48h_precip
        }

        logging.info(f"NWS data fetched: High={today_high}°F, Low={today_low}°F, "
                    f"Cloud={today_cloud_cover}%, Precip today={today_precip}%, "
                    f"Precip tomorrow={tomorrow_precip}%, Precip 48h={max_48h_precip}%")

        return result

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching NWS data: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching NWS data: {e}", exc_info=True)
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    result = fetch_nws('92109')
    print(result)

