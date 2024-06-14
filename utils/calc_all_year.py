import numpy as np
from params import general_params as def_gen_params
from utils.helpers import get_max_consecutive_nan, set_user_params


def calc_all_year(flow_matrix, general_params=def_gen_params):
    key = 'max_nan_allowed_per_year'
    key2 = 'max_consecutive_nan_allowed_per_year'

    params = set_user_params(general_params, def_gen_params)

    max_nan_allowed_per_year = params[key]
    max_consecutive_nan_allowed_per_year = params[key2]

    average_annual_flows = []
    standard_deviations = []
    coefficient_variations = []
    for index, _ in enumerate(flow_matrix[0]):
        average_annual_flows.append(None)
        standard_deviations.append(None)
        coefficient_variations.append(None)
        """Check to see if water year has more than allowed nan or zeros"""
        if np.isnan(flow_matrix[:, index]).sum() > max_nan_allowed_per_year:
            continue
        """Check max consecutive missing days"""
        if get_max_consecutive_nan(flow_matrix[:, index]) > max_consecutive_nan_allowed_per_year:
            continue

        average_annual_flows[-1] = np.nanmean(flow_matrix[:, index])
        standard_deviations[-1] = np.nanstd(flow_matrix[:, index])
        coefficient_variations[-1] = standard_deviations[-1] / average_annual_flows[-1]

    return average_annual_flows, standard_deviations, coefficient_variations

