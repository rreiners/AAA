# weather_api.py
import pandas as pd
import requests
from typing import List, Optional, Dict, Union
from datetime import date, datetime

class ChicagoWeatherAPI:
    """
    A client for fetching weather data for Chicago using the Open-Meteo API.
    Open-Meteo is free for non-commercial use and requires no API key.
    API Documentation: https://open-meteo.com/en/docs
    """
    HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"

    # Default coordinates for Chicago
    CHICAGO_LATITUDE = 41.8781
    CHICAGO_LONGITUDE = -87.6298

    # Common weather variables (see Open-Meteo docs for full list)
    # For hourly: temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation,rain,snowfall,weather_code,pressure_msl,surface_pressure,cloud_cover,et0_fao_evapotranspiration,wind_speed_10m,wind_direction_10m,wind_gusts_10m
    # For daily: weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,daylight_duration,sunshine_duration,precipitation_sum,rain_sum,snowfall_sum,precipitation_hours,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant
    DEFAULT_HOURLY_VARIABLES = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]
    DEFAULT_DAILY_VARIABLES = ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"]


    def __init__(self, latitude: float = CHICAGO_LATITUDE, longitude: float = CHICAGO_LONGITUDE):
        """
        Initializes the ChicagoWeatherAPI client.

        Args:
            latitude: Latitude for the weather data (defaults to Chicago).
            longitude: Longitude for the weather data (defaults to Chicago).
        """
        self.latitude = latitude
        self.longitude = longitude
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "ChicagoWeatherAPI-Client/1.0"})

    def _make_request(self, base_url: str, params: Dict) -> Optional[Dict]:
        """Helper function to make GET requests to the API."""
        try:
            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP error occurred: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"❌ Request error occurred: {req_err}")
        except ValueError as json_err: # Includes JSONDecodeError
            print(f"❌ JSON decoding error: {json_err}")
        return None

    def get_historical_weather(self,
                               start_date: Union[str, date],
                               end_date: Union[str, date],
                               hourly_vars: Optional[List[str]] = None,
                               daily_vars: Optional[List[str]] = None,
                               timezone: str = "America/Chicago") -> Optional[pd.DataFrame]:
        """
        Fetches historical weather data for the specified date range and variables.

        Args:
            start_date: Start date for historical data (YYYY-MM-DD string or date object).
            end_date: End date for historical data (YYYY-MM-DD string or date object).
            hourly_vars: List of hourly weather variables to fetch.
                         Defaults to ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"].
                         Pass an empty list [] for no hourly data if daily_vars are requested.
            daily_vars: List of daily aggregated weather variables to fetch.
                        Defaults to None.
            timezone: Timezone for the data (e.g., "America/Chicago").

        Returns:
            A pandas DataFrame with historical weather data, or None if an error occurs.
            The DataFrame will have a 'time' or 'date' index.
        """
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "timezone": timezone,
        }

        if hourly_vars is None and daily_vars is None: # Default to some hourly if nothing specified
            params["hourly"] = ",".join(self.DEFAULT_HOURLY_VARIABLES)
        elif hourly_vars is not None: # Can be an empty list
             if hourly_vars:
                params["hourly"] = ",".join(hourly_vars)
        
        if daily_vars is not None:
            if daily_vars: # only add if list is not empty
                params["daily"] = ",".join(daily_vars)
            elif "hourly" not in params: # if both are empty, error or fetch default
                 print("⚠️ Both hourly_vars and daily_vars are empty/None. Fetching default hourly data.")
                 params["hourly"] = ",".join(self.DEFAULT_HOURLY_VARIABLES)


        raw_data = self._make_request(self.HISTORICAL_API_URL, params)

        if raw_data:
            if "hourly" in raw_data:
                df = pd.DataFrame(raw_data["hourly"])
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                return df
            elif "daily" in raw_data: # if only daily data was requested and returned
                df = pd.DataFrame(raw_data["daily"])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            else:
                print("⚠️ No 'hourly' or 'daily' data found in the API response.")
                return pd.DataFrame() # Return empty dataframe
        return None

    def get_forecast_weather(self,
                             days: int = 7, # Number of days for forecast
                             hourly_vars: Optional[List[str]] = None,
                             daily_vars: Optional[List[str]] = None,
                             timezone: str = "America/Chicago",
                             past_days: int = 0) -> Optional[pd.DataFrame]:
        """
        Fetches forecast weather data.

        Args:
            days: Number of days to forecast (1 to 16).
            hourly_vars: List of hourly weather variables. Defaults to a common set.
            daily_vars: List of daily weather variables. Defaults to a common set.
            timezone: Timezone for the data.
            past_days: Include number of past days in the forecast response (0 to 92).

        Returns:
            A pandas DataFrame with forecast weather data, or None.
        """
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "forecast_days": days,
            "timezone": timezone,
            "past_days": past_days
        }
        
        used_hourly_vars = hourly_vars if hourly_vars is not None else self.DEFAULT_HOURLY_VARIABLES
        used_daily_vars = daily_vars if daily_vars is not None else self.DEFAULT_DAILY_VARIABLES

        if used_hourly_vars:
            params["hourly"] = ",".join(used_hourly_vars)
        if used_daily_vars:
            params["daily"] = ",".join(used_daily_vars)
        
        if not used_hourly_vars and not used_daily_vars:
            print("⚠️ No hourly or daily variables specified for forecast. Fetching default hourly.")
            params["hourly"] = ",".join(self.DEFAULT_HOURLY_VARIABLES)

        raw_data = self._make_request(self.FORECAST_API_URL, params)

        if raw_data:
            # Open-Meteo forecast can return both hourly and daily.
            # For simplicity, we'll prioritize and return the hourly DataFrame if available.
            # A more sophisticated handling could return a dictionary of DataFrames.
            if "hourly" in raw_data and raw_data["hourly"]:
                df = pd.DataFrame(raw_data["hourly"])
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                # You can also process raw_data["daily"] if needed and merge or return separately
                return df
            elif "daily" in raw_data and raw_data["daily"]:
                df = pd.DataFrame(raw_data["daily"])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            else:
                print("⚠️ No 'hourly' or 'daily' data found in the forecast API response.")
                return pd.DataFrame()
        return None

    def close(self):
        """Closes the underlying requests session."""
        self.session.close()