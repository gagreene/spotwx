# -*- coding: utf-8 -*-
"""
Created on Mon Aug 6 12:00:00 2024

@author: Gregory A. Greene
"""
__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import re
import warnings

# Suppress SyntaxWarnings specifically
warnings.filterwarnings('ignore', category=SyntaxWarning)

class SpotWx:
    """
    Class to request weather forecast data from SpotWx.
    """
    def __init__(
            self,
            csv_path: str,
            model_request: str,
            lat: float,
            lon: float,
            timezone: str,
            display: str = 'table_prometheus'
    ):
        self.csv_path = csv_path
        self.model_request = model_request
        self.lat = lat
        self.lon = lon
        self.timezone = timezone
        self.display = display
        self.URL = None
        self.title = None
        self.zone = None

        self.model_dict = {
            'hrdps': 'hrdps_1km_west',
            'hrdps_continental': 'hrdps_continental',
            'rdps': 'rdps_10km',
            'gdps': 'gem_glb_15km',
            'geps': 'geps_0p5_raw',
            'rap': 'rap_awp',
            'nam': 'nam_awphys',
            'sref': 'sref_pgrb',
            'gfs': 'gfs_pgrb2',
            'gfs_uv_index': 'gfs_uv',
            'short_meteocode': 'meteocode',
            'ext_meteocode': 'meteocode'
        }

        self.title_dict = {
            'short_meteocode': 'FPVR14',
            'ext_meteocode': 'FPVR54'
        }

        self.timezone_list = [
            # Canada-specific time zones
            'America/Vancouver', 'America/Edmonton', 'America/Regina', 'America/Winnipeg',
            'America/Toronto', 'America/Montreal', 'America/St_Johns', 'America/Halifax',
            'America/Goose_Bay', 'America/Whitehorse', 'America/Yellowknife', 'America/Rankin_Inlet',
            'America/Iqaluit', 'America/Cambridge_Bay', 'America/Coral_Harbour'
        ]

        self.display_list = [
            'table', 'table_prometheus'
        ]

    def _verify_inputs(self) -> None:
        """
        Function to verify the SpotWx request input parameters
        :return: None
        """
        # csv_path
        if not isinstance(self.csv_path, str):
            raise TypeError('The "csv_path" input parameter must be a str datatype')
        elif not self.csv_path.endswith('.csv'):
            raise ValueError('The "csv_path" input parameter must be a path to a csv file, '
                             'including a ".csv" extension')
        # model_request
        if not isinstance(self.model_request, str):
            raise TypeError('The "model_request" input parameter must be a str datatype')
        elif self.model_request not in list(self.model_dict.keys()):
            raise ValueError('The "model_request" input parameter must be one of the following values:'
                             f'\n{list(self.model_dict.keys())}')
        # lat
        if not isinstance(self.lat, float):
            raise ValueError('The "lat" input parameter must be a float datatype')
        # long
        if not isinstance(self.lon, float):
            raise ValueError('The "lon" input parameter must be a float datatype')
        # timezone
        if not isinstance(self.timezone, str):
            raise TypeError('The "timezone" input parameter must be a str datatype')
        elif self.timezone not in self.timezone_list:
            raise ValueError('The "timezone" input parameter must be one of the following values:'
                             f'\n{self.timezone_list}')
        # display
        if not isinstance(self.display, str):
            raise TypeError('The "display" input parameter must be a str datatype')
        elif self.display not in self.display_list:
            raise ValueError('The "display" input parameter must be one of the following values:'
                             f'\n{self.display_list}')

        return

    def _create_url(self) -> None:
        """
        Function to generate a url to request data through the SpotWx REST API
        :return: None
        """
        self.model = self.model_dict.get(self.model_request, None)
        self.title = self.title_dict.get(self.model_request, None)

        self.url = 'https://spotwx.com/products/grib_index.php?'
        if self.model:
            self.url += f'model={self.model}'
        if self.title:
            self.url += f'&title={self.title}'
        if self.lat:
            self.url += f'&lat={self.lat}'
        if self.lon:
            self.url += f'&lon={self.lon}'
        if self.zone:
            self.url += f'&zone={self.zone}'
        if self.timezone:
            self.url += f'&tz={self.timezone}'
        if self.display:
            self.url += f'&display={self.display}'

        return

    def _get_csv(self) -> None:
        """
        Function to generate a csv from the SpotWx requested data
        :return: None
        """
        # Send a GET request to the API
        response = requests.get(self.url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the script tag that contains the aDataSet variable
            script = soup.find('script', text=re.compile(r'var aDataSet ='))

            if script:
                # Extract the JSON-like data from the script tag
                script_text = script.string
                json_text = re.search(r'var aDataSet = (\[.*?\]);', script_text, re.DOTALL).group(1)

                # Replace single quotes with double quotes to make it valid JSON
                json_text = json_text.replace("'", '"')

                # Convert the JSON-like string to a Python list
                data = json.loads(json_text)

                # Define the column headers (based on the HTML content you provided)
                headers = ['HOURLY', 'HOUR', 'TEMP', 'RH', 'WD', 'WS', 'PRECIP']

                # Convert the data to a pandas DataFrame
                df = pd.DataFrame(data, columns=headers)

                # Save the DataFrame as a CSV file
                df.to_csv(self.csv_path, index=False)
                print('CSV file has been saved successfully.')
            else:
                print('JavaScript variable "aDataSet" not found in the HTML content.')
        else:
            print(f'Failed to retrieve data. Status code: {response.status_code}')

        return

    def getSpotWx(self):
        self._verify_inputs()
        self._create_url()
        self._get_csv()


if __name__ == '__main__':
    if len(sys.argv[1:]) != 6:
        print('Six parameters are required to request a SpotWx forecast dataset (as csv):\n'
              '[csv_path, model_request, lat, lon, display].')
        sys.exit(1)

    # Get input parameters from the console
    _csv_path, _model_request, _lat, _lon, _timezone, _display = sys.argv[1:]

    SpotWx(
        csv_path=_csv_path,
        model_request=_model_request,
        lat=_lat,
        lon=_lon,
        timezone=_timezone,
        display=_display).getSpotWx()
