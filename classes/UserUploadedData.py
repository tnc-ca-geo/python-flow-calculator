from classes.AbstractGage import AbstractGage
import csv
from classes.Exceptions.not_enough_data import NotEnoughDataError

class UserUploadedData(AbstractGage):
    def __init__(self, file_name, download_directory,measurement_unit='cfs', longitude = None, latitude = None, comid = None, selected_calculator = None):
        super().__init__(gage_id=file_name, measurement_unit = measurement_unit, longitude = longitude, latitude = latitude, comid = comid, download_directory = download_directory)
        
    def download_metadata(self):
        pass
    
    def save_daily_data(self):
        # the data has already been saved but other objects do a quick check that there is enough data in here aswell
        # will raise file not found if it does not exist as intended
        with open(self.download_directory, mode='r', newline='') as file:
            reader = csv.reader(file)
            row_count = sum(1 for row in reader)  # Count each row
        if row_count < 368:
            raise NotEnoughDataError(f'user uploaded file at directory {self.download_directory} does not have enough data')


    def get_comid(self):
        if (self.comid is None) or (self.comid == ''):
            super().get_comid()
        
        return self.comid

    def __str__(self):
        """
        Return a string representation of the User uploaded data.
        """
        return f"Data File Name: {self.gage_id}, Location: {self.latitude}, {self.longitude}, Measurement Unit: {self.measurement_unit}"
        