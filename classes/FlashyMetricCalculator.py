from classes.MetricCalculator import Calculator
from utils.calc_UCD_alt_dry_spring_timings import Altered_Spring_Recession
from utils.calc_UCD_alt_wet_fall_timings import Altered_Fall_Wet_Timing
from params import flashy_params

class FlashyCalculator(Calculator):
    # To be in line with python documentation https://docs.python.org/3/library/exceptions.html#NotImplementedError
    # "Note: It should not be used to indicate that an operator or method is not meant to be supported at all – in that case either leave the operator / method undefined or, if a subclass, set it to None."
    # We will set methods that do not be planned to be implemented to none
    # This is because the flashy calculator implements several functionalities from the reference calculator in a single function.
    # realistically this means there likely should have been a abstract super class that only includes implementations of the functions that all calculators use the same thing for and abstract definitions of the others or no definition at all for the below ones that needed to be set to none.
    # however due to the fact that there are no plans as far as I am aware to make a third calculator this more simple structure will probably be fine and more maintainable for individuals not familiar with abstract classes. Despite the weirdness of assigning functions to None
    spring_transition_duration = None
    _format_spring_transition_duration = None

    spring_transition_roc = None
    _format_spring_transition_roc = None

    start_of_summer = None
    _format_start_of_summer = None

    spring_transition_timing_magnitude = None
    _format_spring_transition_magnitude = None
    
    def __init__(self, flow_matrix, year_ranges, flow_class, first_year, start_date):
       
       params = {}
       params['general_params'] = flashy_params
       params['winter_params'] = flashy_params
       super().__init__(flow_matrix, year_ranges, flow_class, first_year, start_date, params = params)


    def dry_spring_timings(self):
        # combines the functionality of start_of_summer, spring_transition_timing_magnitude, spring_transition_duration and spring_transition_roc from the reference calculator
        output_dict = Altered_Spring_Recession(self.flow_matrix)
        self._summer_timings = output_dict.get("DS_Tim")
        self._spring_timings = output_dict.get("timings_water")
        return self._format_dry_spring_timings(output_dict)

    def _format_dry_spring_timings(self, dictionary):
        start_of_summer = dictionary.pop('DS_Tim', None)
        return dictionary, start_of_summer

    def fall_flush_timings_durations(self):
        if not self._summer_timings:
            self.dry_spring_timings()
        output_dict = Altered_Fall_Wet_Timing(self.flow_matrix, self._summer_timings)
        self._fall_timings = output_dict.get('timings_water')
        self._fall_wet_timings = output_dict.get('Wet_Tim')
        return self._format_fall_flush(output_dict)
    
    def _format_fall_flush(self, dictionary):
        start_of_wet = dictionary.pop('Wet_Tim', None)
        return dictionary, start_of_wet