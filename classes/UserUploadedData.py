from classes.AbstractGage import AbstractGage

class UserUploadedData(AbstractGage):
    def __init__(self, file_name, download_directory,measurement_unit='cfs', longitude = None, latitude = None, comid = None, selected_calculator = None):
        super().__init__(gage_id=file_name, measurement_unit = measurement_unit, longitude = longitude, latitude = latitude, comid = comid, download_directory = download_directory)
        
    def download_metadata(self):
        pass
    
    def save_daily_data(self):
        pass

    def get_comid(self):
        if (self.comid is None) or (self.comid == ''):
            super().get_comid()
        
        return self.comid

    def __str__(self):
        """
        Return a string representation of the User uploaded data.
        """
        return f"Data File Name: {self.gage_id}, Location: {self.latitude}, {self.longitude}, Measurement Unit: {self.measurement_unit}"
        