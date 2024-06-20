from abc import ABC, abstractmethod
from pynhd import NLDI

class AbstractGage(ABC):
    def __init__(self, gage_id, measurement_unit='cfs', longitude=None, latitude=None, comid=None, flow_class = None, download_directory = None, selected_calculator = None):
        self.gage_id = gage_id
        self.measurement_unit = measurement_unit
        self.readings = []
        self.longitude = longitude
        self.latitude = latitude
        self.comid = comid
        self.flow_class = flow_class
        self.download_directory = download_directory
        self.selected_calculator = selected_calculator

    @abstractmethod
    def download_metadata(self):
        pass

    @abstractmethod
    def save_daily_data(self):
        pass

    def get_comid(self):
        nldi = NLDI()
        # this package can also be used for other physical characteristics down the line if needed pretty neat (upstream stuff etc)
        comid_closest = nldi.comid_byloc((self.longitude, self.latitude))
        self.comid = comid_closest['comid'].iloc[0]

    def __str__(self):
        """
        Return a string representation of the Gage.
        """
        return f"Gage ID: {self.gage_id}, Location: {self.latitude}, {self.longitude}, Measurement Unit: {self.measurement_unit}"
