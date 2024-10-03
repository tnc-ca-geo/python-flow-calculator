import csv
import dataretrieval.nwis as nwis
import os
from classes.AbstractGage import AbstractGage
from classes.Exceptions.not_enough_data import NotEnoughDataError

class USGSGage(AbstractGage):
    def __init__(self, gage_id):
        """
        Initialize a USGS Gage instance.

        Parameters:
        - gage_id (str): The unique identifier for the USGS Gage. Expected to be 8 or more characters and prepended with 0's for id's with less characters such as '9424050'
        - measurement_unit (str, optional): The measurement unit for the gage readings (default is 'cfs').
        """
        super().__init__(gage_id)
        
    def download_metadata(self):
        """
        Download metadata for the USGS Gage, including latitude and longitude.

        Uses the nwis package to retrieve information about the specified gage and updates
        the latitude and longitude attributes of the USGS Gage instance.
        """
        if self.gage_id is not None:
            df = nwis.get_info(sites=self.gage_id)
            self.latitude = df[0]['dec_lat_va'].iloc[0]
            self.longitude = df[0]['dec_long_va'].iloc[0]
    
    def save_daily_data(self):
        """
        Save daily flow data for the USGS Gage to a CSV file.

        Uses the nwis package to retrieve daily flow data, transforms the data, and saves it
        to a CSV file named '{gage_id}_data.csv' in the 'gage_data' folder. If tidally filtered data is availble that will be used instead of normal discharge

        Returns:
        - csv_file_path (str): The path to the saved CSV file.
        """
        df = nwis.get_record(sites = self.gage_id, service="dv", parameterCd = "72137", statCd="00003", start="1800-10-01")
        if df.empty or len(df.index) < 365:
            df = nwis.get_record(sites = self.gage_id, service="dv", parameterCd = "00060", statCd="00003", start="1800-10-01")
        if df.empty:
            raise Exception(f'No data found for {self.gage_id} is this a valid USGS gage? (ensure that gages less than 9 gigits long are front padded with 0)')
        if len(df.index) < 365:
            raise NotEnoughDataError(f"There was little data available for {self.gage_id}")
            
        self.start_date = df.index[0]
        # mapping both 72137_Mean and 00060_Mean to flow because we know there will only be 1 or the other
        df = df.rename(columns={'72137_Mean': 'flow', '00060_Mean': 'flow', 'datetime': 'date', 'site_no': 'gage', '00060_Mean_cd': 'flow_flag', '72137_Mean_cd': 'flow_flag'})
        folder_path = os.path.join(os.getcwd(), 'gage_data')
        csv_file_path = os.path.join(folder_path, f'{self.gage_id}_data.csv')
        df.to_csv(csv_file_path, index_label='date', date_format='%m/%d/%Y')
        self.download_directory = csv_file_path

    def get_comid(self):
        """
        Get the ComID (Common Identifier) associated with the USGS Gage.

        Firstly checks the lookup csv in extra_info/ for a matching gage_id to comid

        As a second check If the ComID is not already assigned, it uses the NLDI package to find the ComID based on
        the gage's latitude and longitude and updates the comid attribute.

        Returns:
        - comid (str): The ComID associated with the USGS Gage.
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
        Return a string representation of the USGS Gage.
        """
        
        return f"USGS Gage ID: {self.gage_id}, Location: {self.latitude}, {self.longitude}, Measurement Unit: {self.measurement_unit}"
        