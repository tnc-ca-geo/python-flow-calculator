import pandas as pd
import requests
from io import StringIO
import csv
from classes.Exceptions.not_enough_data import NotEnoughDataError
import os
from datetime import datetime
from utils.helpers import try_float
from bs4 import BeautifulSoup
from classes.AbstractGage import AbstractGage

class CDECGage(AbstractGage):
    def __init__(self, gage_id):
        """
        Initializes a CDECGage object.

        Args:
            gage_id (str): The unique identifier of the CDEC gage.
            measurement_unit (str): The unit of measurement for the data collected by the gage (default is 'cfs').
            longitude (float): The longitude coordinate of the gage location.
            latitude (float): The latitude coordinate of the gage location.
            comid (str): The COMID (Common Identifier) associated with the gage, used for identification within hydrological datasets.
            flow_class (int): The flow classification of the stream where the gage is located (1-9).
        """
        super().__init__(gage_id)

        
    def download_metadata(self):
        """
        Downloads metadata for the CDEC gage from the CDEC website and updates latitude and longitude attributes accordingly.
        """     
        url =  f'http://cdec.water.ca.gov/dynamicapp/staMeta?station_id={self.gage_id}'
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')
            table_data = []
            
            lat_row = 0
            lat_ind = 0
            lng_row = 0
            lng_ind = 0
            
            if table:

                for row_index, row in enumerate(table.find_all('tr')):
                    row_data = []
                    for cell_index, cell in enumerate(row.find_all(['td', 'th'])):
                        cell_text = cell.get_text(strip=True)
                        if cell_text == 'Latitude':
                            lat_row = row_index
                            lat_ind = cell_index
                        elif cell_text == 'Longitude':
                            lng_row = row_index
                            lng_ind = cell_index
                        row_data.append(cell_text)
                    table_data.append(row_data)
            
            # some assumptions here about the structure of the table
            # assuming that it will always be Latitude, {lat_value}
            # ie if they are to use a different way to identify what the latitude is such as LAT
            # or if they transpose the table this will fail but it should not be too bad to fix
            
            self.latitude = float(table_data[lat_row][lat_ind + 1][:-1])
            self.longitude = float(table_data[lng_row][lng_ind + 1][:-1])

        else:
            raise Exception(f'Unable to retrieve station metadata for CDEC id {self.gage_id}')
    
    def save_daily_data(self):
        """
        Saves daily flow data for the CDEC gage to a CSV file.
        """
        today = datetime.today().strftime('%Y-%m-%d')
        cdec_param_ids_to_try = [{'param_id':'20', 'duration_code':'D'}, {'param_id':'20', 'duration_code':'H'}, {'param_id':'41','duration_code':'D'}, {'param_id':'20', 'duration_code':'E'}, {'param_id':'165', 'duration_code':'E'}]
        had_data_but_not_enough = False
        for dict in cdec_param_ids_to_try:
        
            url = f'http://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={self.gage_id}&SensorNums={dict["param_id"]}&dur_code={dict["duration_code"]}&Start=1800-10-01&End={today}'
            response = requests.get(url)
            if response.status_code == 200:
                
                csv_data = response.text
                columns_to_read = ['DATE TIME', 'VALUE']
                column_types = {'DATE TIME': str}
                custom_converters = {'VALUE': try_float}
                df = pd.read_csv(StringIO(csv_data), dtype = column_types, usecols=columns_to_read, converters=custom_converters)
                if df.empty:
                    continue
                if len(df.index) < 365:
                    had_data_but_not_enough = True
                    continue
                df = df.dropna(subset=['VALUE'])
                df['DATE TIME'] = pd.to_datetime(df['DATE TIME'], format='%Y%m%d %H%M').dt.date
                df = df.groupby('DATE TIME')['VALUE'].mean().reset_index()
                df = df.rename(columns={'DATE TIME': 'date', 'VALUE': 'flow'})
                df['date'] = pd.to_datetime(df['date'])

                folder_path = os.path.join(os.getcwd(), 'gage_data')
                csv_file_path = os.path.join(folder_path, f'{self.gage_id}.csv')
                df.to_csv(csv_file_path, index=False, date_format='%m/%d/%Y')
                self.download_directory = csv_file_path
                return
            else:
                continue
        if had_data_but_not_enough:
            raise NotEnoughDataError(f"Gage: {self.__str__} had some data available but not enough to proceed")
        else:
            raise Exception(f"Failed to fetch data from cdec with url: {url}. For parameters 20 and 41. Status code:{response.status_code}")


    def get_comid(self):
        """
        Retrieves the COMID associated with the CDEC gage from a CSV file, if not already provided, and updates the comid attribute.
        """
        if self.comid not in (None, ''):
            return self.comid
        
        target_id = self.gage_id
        

        
        folder_path = os.path.join(os.getcwd(), 'extra_info')
        csv_file_path = os.path.join(folder_path, f'filtered_stream_gages_v3c_20240311.csv')
        match_row = None
        with open(csv_file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['siteid'] == target_id:
                    match_row = row

        if match_row:
            self.comid = match_row['comid_medres']


        if (self.comid is None) or (self.comid == ''):
            super().get_comid()
        
        return self.comid

    def __str__(self):
        """
        Return a string representation of the CDEC Gage.
        """
        return f"CDEC ID: {self.gage_id}, Location: {self.latitude}, {self.longitude}, Measurement Unit: {self.measurement_unit}"
       