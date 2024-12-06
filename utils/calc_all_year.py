import numpy as np
from params import general_params as def_gen_params
from utils.helpers import get_max_consecutive_nan, set_user_params


def calc_all_year(flow_matrix, first_year, general_params=def_gen_params):
    key = 'max_nan_allowed_per_year'
    key2 = 'max_consecutive_nan_allowed_per_year'
    key3 = 'max_zero_allowed_per_year'
    key4 = 'min_flow_rate'

    params = set_user_params(general_params, def_gen_params)

    max_nan_allowed_per_year = params[key]
    max_consecutive_nan_allowed_per_year = params[key2]
    max_zero_allowed_per_year = params[key3]
    min_flow_rate = params[key4]

    skipped_years_message = ''

    average_annual_flows = []
    standard_deviations = []
    coefficient_variations = []
    for index, _ in enumerate(flow_matrix[0]):
        max_days = 365
        year = first_year + index
        # this is logic for leap years, if something passes then it is a leap year
        if year % 4 == 0 and (year % 400 == 0 or year % 100 != 0) == True:
            max_days = 366
        num_nan = min(np.isnan(flow_matrix[:, index]).sum(),max_days)
        num_consec_nan = min(get_max_consecutive_nan(flow_matrix[:, index]),max_days)
        num_zeroes = min(np.count_nonzero(flow_matrix[:, index] == 0),max_days)
        max_flow = max(flow_matrix[:, index])
        average_annual_flows.append(None)
        standard_deviations.append(None)
        coefficient_variations.append(None)
        if num_nan > max_nan_allowed_per_year:
            skipped_years_message = skipped_years_message + f'{year} skipped because number of nan days ({num_nan}) exceeds the max allowed nan days per year ({max_nan_allowed_per_year})\n'
            continue
        elif num_consec_nan > max_consecutive_nan_allowed_per_year:
            skipped_years_message = skipped_years_message + f'{year} skipped because number of consecutive nan days ({num_consec_nan}) exceeds the max allowed consecutive nan days per year ({max_consecutive_nan_allowed_per_year})\n'
            continue
        elif num_zeroes > max_zero_allowed_per_year:
            skipped_years_message = skipped_years_message + f'{year} skipped because number of zero flow days ({num_zeroes}) exceeds the max allowed zero flow days per year ({max_zero_allowed_per_year})\n'            
            continue
        elif max_flow < min_flow_rate:
            skipped_years_message = skipped_years_message + f'{year} skipped because max flow rate ({max_flow}) is less then the minimum required flow ({min_flow_rate})\n'            
            continue
        

        average_annual_flows[-1] = np.nanmean(flow_matrix[:, index])
        standard_deviations[-1] = np.nanstd(flow_matrix[:, index])
        coefficient_variations[-1] = standard_deviations[-1] / average_annual_flows[-1]

    return average_annual_flows, standard_deviations, coefficient_variations, skipped_years_message

