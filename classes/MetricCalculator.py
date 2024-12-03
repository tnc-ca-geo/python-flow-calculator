import numpy as np
import itertools
from datetime import datetime
from utils.calc_drh import calc_drh
from utils.calc_all_year import calc_all_year
from utils.calc_winter_highflow import calc_winter_highflow_annual
from utils.calc_summer_baseflow import calc_start_of_summer, calc_summer_baseflow_durations_magnitude
from utils.calc_fall_flush import calc_fall_flush_timings_durations
from utils.calc_spring_transition import calc_spring_transition_timing_magnitude, calc_spring_transition_roc, calc_spring_transition_duration
from utils.calc_fall_winter_baseflow import calc_fall_winter_baseflow
from utils.calc_new_low_flow_metrics import calc_new_low_flow_metrics
from utils.helpers import remove_offset_from_julian_date, fill_year_array, replace_nan
from params import general_params, winter_params, spring_params, summer_params, fall_params


class Calculator:

    exceedance_percent = [2, 5, 10, 20, 50]

    def __init__(self, flow_matrix, year_ranges, flow_class, first_year, start_date):
        self.flow_matrix = flow_matrix
        self.year_ranges = fill_year_array(list(set(year_ranges)))
        self.flow_class = flow_class
        self.first_year = first_year
        self.start_date = start_date
        self.julian_start_date = datetime.strptime(
            "{}/2001".format(start_date), "%m/%d/%Y").timetuple().tm_yday
        


    def new_low_flow_metrics(self):
        if not self._summer_timings:
            self.start_of_summer()
        low_min_avgs, low_min_indices, classification, zeros_per_year, first_zero, classification_per_year = calc_new_low_flow_metrics(self.flow_matrix, self.first_year, self._summer_timings)
        return self._format_low_flow(low_min_avgs, low_min_indices, classification, zeros_per_year, first_zero, classification_per_year)

    def _format_low_flow(self, low_min_avgs, low_min_indices, classification, zeros_per_year, first_zero, classification_per_year):
            results = {}
            results_general = {}
            results["low_min_avgs"] = low_min_avgs

            results["low_min_date"] = low_min_indices
            results["first_zero"] = first_zero
            results["zeros_per_year"] = zeros_per_year
            results_general["Overall_Int_Class"] = np.full_like(classification_per_year, classification).tolist()
            results_general["Int_Class"] = classification_per_year
            return results, results_general
    
    def get_DRH(self):
        drh = calc_drh(self.flow_matrix)
        return self._format_drh(drh)

    def _format_drh(self,drh):
        return drh
        
    
    def all_year(self):
        params = self.params['general_params'] if self.params else general_params
        average_annual_flows, standard_deviations, coefficient_variations, skipped_years_message = calc_all_year(
            self.flow_matrix, self.first_year, params)
        return self._format_all_year(average_annual_flows, standard_deviations, coefficient_variations), skipped_years_message

    def _format_all_year(self,average_annual_flows,standard_deviations,coefficient_variations):
        results = {}
        results["average_annual_flows"] = average_annual_flows
        results["standard_deviations"] = standard_deviations
        results["coefficient_variations"] = coefficient_variations 
        return results
    
    def winter_highflow_annual(self):
        params = self.params['winter_params'] if self.params else winter_params

        winter_timings, winter_durations, winter_frequencys, winter_magnitudes = calc_winter_highflow_annual(
            self.flow_matrix, params)
        winter_timings_dict = {}
        winter_durations_dict = {}
        winter_frequencys_dict = {}
        winter_magnitudes_dict = {}

        for percent in self.exceedance_percent:
            winter_timings_dict[percent] = winter_timings[percent]
            winter_durations_dict[percent] = list(
                map(lambda x: int(x) if isinstance(x, np.int64) else x, winter_durations[percent]))
            winter_frequencys_dict[percent] = list(
                map(lambda x: int(x) if isinstance(x, np.int64) else x, winter_frequencys[percent]))
            winter_magnitudes_dict[percent] = winter_magnitudes[percent]
        return self._format_winter_highflow(winter_timings_dict, winter_durations_dict, winter_frequencys_dict, winter_magnitudes_dict)

    def _format_winter_highflow(self, winter_timings, winter_durations, winter_frequencys, winter_magnitudes):
        results = {}
        key_maps = {50: "fifty", 20: "twenty", 10: "ten", 5: "five", 2: "two"}
        winter_timings_dict = {}
        winter_durations_dict = {}
        winter_magnitudes_dict = {}
        winter_frequencys_dict = {}
        for key, value in key_maps.items():
            winter_timings[value] = list(map(
                remove_offset_from_julian_date, winter_timings[key], itertools.repeat(self.julian_start_date)))
            winter_timings[value +
                        '_water'] = winter_timings[key]
            winter_durations_dict[value] = winter_durations[key]
            winter_magnitudes_dict[value] = winter_magnitudes[key]
            winter_frequencys_dict[value] = winter_frequencys[key]

        results["timings"] = winter_timings_dict
        results["magnitudes"] = winter_magnitudes_dict
        results["durations"] = winter_durations_dict
        results["frequencys"] = winter_frequencys_dict
        return results

    def start_of_summer(self):

        params = self.params['summer_params'] if self.params else summer_params
        summer_timings = calc_start_of_summer(
            self.flow_matrix, self.flow_class, params)
        self._summer_timings = summer_timings
        return self._format_start_of_summer(summer_timings)

    def _format_start_of_summer(self,summer_timings):
       return summer_timings
    
    def fall_flush_timings_durations(self):
        if not self._summer_timings:
            self.start_of_summer()
        params = self.params['fall_params'] if self.params else fall_params
        fall_timings, fall_magnitudes, fall_wet_timings, fall_durations = calc_fall_flush_timings_durations(
            self.flow_matrix, self._summer_timings, self.flow_class, params)
        self._fall_timings = fall_timings
        self._fall_wet_timings = fall_wet_timings
        return self._format_fall_flush(fall_timings,fall_magnitudes,fall_wet_timings,fall_durations)
    
    def _format_fall_flush(self,fall_timings,fall_magnitudes,fall_wet_timings,fall_durations):
        results = {}
        results["magnitudes"] = fall_magnitudes
        results["timings_water"] = fall_timings
        results["durations"] = fall_durations
        return results, fall_wet_timings

    def summer_baseflow_durations_magnitude(self):
        if not self._summer_timings:
            self.start_of_summer()
        if not self._fall_wet_timings:
            self.fall_flush_timings_durations()
        if not self._fall_timings:
            self.fall_flush_timings_durations()
        summer_90_magnitudes, summer_50_magnitudes, summer_flush_durations, summer_wet_durations, summer_no_flow_counts = calc_summer_baseflow_durations_magnitude(
            self.flow_matrix, self._summer_timings, self._fall_timings, self._fall_wet_timings)
        return self._format_summer_baseflow(summer_90_magnitudes,summer_50_magnitudes,summer_flush_durations,summer_wet_durations,summer_no_flow_counts)

    def _format_summer_baseflow(self,summer_90_magnitudes,summer_50_magnitudes,summer_flush_durations,summer_wet_durations,summer_no_flow_counts):
        results = {}
        results["magnitudes_fifty"] = summer_50_magnitudes
        results["magnitudes_ninety"] = summer_90_magnitudes
        #results["summer_flush_durations"] = summer_flush_durations
        results["durations_wet"] = summer_wet_durations
        results["no_flow_counts"] = summer_no_flow_counts
        return results

    def spring_transition_timing_magnitude(self):
        if not self._summer_timings:
            self.start_of_summer()
        params = self.params['spring_params'] if self.params else spring_params
        spring_timings, spring_magnitudes = calc_spring_transition_timing_magnitude(
            self.flow_matrix, self.flow_class, self._summer_timings, params)
        self._spring_timings = spring_timings
        return self._format_spring_transition_magnitude(spring_timings,spring_magnitudes)
    
    def _format_spring_transition_magnitude(self,spring_timings, spring_magnitudes):
        results = {}
        results["magnitudes"] = spring_magnitudes
        results["timings_water"] = spring_timings
        return results

    def spring_transition_duration(self):
        if not self._summer_timings:
            self.start_of_summer()
        spring_durations = calc_spring_transition_duration(
            self._spring_timings, self._summer_timings)
        return self._format_spring_transition_duration(spring_durations)

    def _format_spring_transition_duration(self, spring_durations):
        return spring_durations


    def spring_transition_roc(self):
        if not self._summer_timings:
            self.start_of_summer()
        spring_rocs = calc_spring_transition_roc(
            self.flow_matrix, self._spring_timings, self._summer_timings)
        return self._format_spring_transition_roc(spring_rocs)

    def _format_spring_transition_roc(self, spring_rocs):
        return spring_rocs

    def fall_winter_baseflow(self):
        if not self._fall_wet_timings:
            self.fall_flush_timings_durations()
        if not self._spring_timings:
            self.spring_transition_timing_magnitude()
        wet_baseflows_10, wet_baseflows_50, wet_bfl_durs, wet_baseflows = calc_fall_winter_baseflow(
            self.flow_matrix, self._fall_wet_timings, self._spring_timings)    
        return self._format_fall_winter_baseflow(wet_baseflows,wet_baseflows_10,wet_baseflows_50,wet_bfl_durs)
    
    def _format_fall_winter_baseflow(self, wet_baseflows,wet_baseflows_10,wet_baseflows_50,wet_bfl_durs):
        results = {}
        # results["baseflows"] =wet_baseflows
        results["baseflows_10"] = wet_baseflows_10
        results["baseflows_50"] = wet_baseflows_50
        results["bfl_durs"] = wet_bfl_durs
        return results
    
    def calc_RBFI(self):
        flow_array =  self.flow_matrix.flatten('F')
        flow_array = replace_nan(flow_array)
        diffs = np.abs(np.diff(flow_array))
        sum_diffs = np.sum(diffs)
        sum_flows = np.sum(flow_array)
        return sum_diffs / sum_flows