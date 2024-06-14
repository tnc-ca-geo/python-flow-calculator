import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
from numpy import NaN, Inf, arange, isscalar, asarray, array

def fill_year_array(years):
    complete_years = list(range(min(years), max(years) + 1))
    missing_years = sorted(set(complete_years) - set(years))
    filled_years = sorted(years + missing_years)
    return filled_years

def set_user_params(user_params, def_params):
    for key in def_params.keys():
        if key in user_params.keys():
            def_params[key] = user_params[key]

    return def_params

def calculate_average_each_column(matrix):
    average = []

    index = 0
    for _ in matrix[0]:
        average.append(np.nanmean(matrix[:, index]))
        index = index + 1

    return average

#helper function to print a numpy array without scientific notation to the desired precision
def GFG(arr,prec):
    np.set_printoptions(suppress=True,precision=prec)
    print(arr)


def median_of_time(lt):
    n = len(lt)
    if n < 1:
        return None
    elif n % 2 ==  1:
        return lt[n//2].start_date
    elif n == 2:
        first_date = lt[0].start_date
        second_date = lt[1].start_date
        return (first_date + second_date) / 2
    else:
        first_date = lt[n//2 - 1].start_date
        second_date = lt[n//2 + 1].start_date
        return (first_date + second_date) / 2

def try_float(x):
    """
    Helper for converting mixed columns to floats and assigning NAN to non numeric entires
    """
    try:
        return float(x)
    except ValueError:
        return float('nan')

def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    """
    maxtab = []
    mintab = []

    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        raise Exception('Input vectors v and x must have same length')

    if not isscalar(delta):
        raise Exception('Input argument delta must be a scalar')

    if delta < 0:
        raise Exception('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)

def replace_nan(flow_data):
    for index, flow in enumerate(flow_data):
        if index == 0 and np.isnan(flow):
            flow_data[index] = 0
        elif np.isnan(flow):
            flow_data[index] = flow_data[index-1]
    return flow_data

def get_max_consecutive_nan(flow_data):
    max_nan = 0
    for flow in flow_data:
        if np.isnan(flow):
            current_count += 1
            max_nan = max(max_nan, current_count)
        else:
            current_count = 0
    return max_nan

def get_date_from_offset_julian_date(row_number, year, start_date):
    start_year = year
    end_year = year + 1
    julian_start_date_start_year = datetime.strptime("{}/{}".format(start_date, start_year), "%m/%d/%Y").timetuple().tm_yday
    if np.isnan(row_number):
        return None
    row_number = int(row_number)
    if start_year % 4 == 0:
        days_in_year_start = 366
    else:
        days_in_year_start = 365

    if row_number <= days_in_year_start - julian_start_date_start_year:
        current_year = start_year
        date_delta = julian_start_date_start_year + row_number
        current_date = datetime(current_year, 1, 1) + timedelta(date_delta - 1)
    else:
        current_year = end_year
        date_delta = row_number - days_in_year_start + julian_start_date_start_year - 1
        current_date = datetime(current_year, 1, 1) + timedelta(date_delta)

    return current_date.strftime('%m/%d/%Y')

def crossings_nonzero_all(data):
    non_zero_array = []
    for index, element in enumerate(data):
        if index == len(data) - 5:
            return non_zero_array
        elif data[index + 1] > 0 and element < 0 :
            non_zero_array.append(index)
        elif data[index + 1] < 0 and element > 0 :
            non_zero_array.append(index)


def find_index(arr, item):
    for index, element in enumerate(arr):
        if element == item:
            return index

def comid_to_class(comid):
    
    comid = int(comid)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir))
    path_to_class_file = os.path.join(parent_dir, "extra_info", "comid_to_stream_class.csv")   
    df = pd.read_csv(path_to_class_file)
    filtered_row = df[(df['comid'] == comid)]
    if filtered_row.empty:
        return None

    data = filtered_row['class'].iloc[0]
    return int(data)

def comid_to_wyt(comid, water_year):

    comid = int(comid)
    water_year = int(water_year)

    if water_year < 1951 or water_year > 2023:
        return 'unknown'
    water_year = water_year - 1951

    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir))
    path_to_wyt_file = os.path.join(parent_dir, "extra_info", "comid_to_wyt.csv")    
    df = pd.read_csv(path_to_wyt_file)
    filtered_row = df[(df['comid'] == comid)]
    if filtered_row.empty:
        return 'unknown'
    
    data = filtered_row['compressed_wyt'].iloc[0]
    data_str = str(data)
    wyt_encoded = data_str[water_year]
    mapping_dict = {'0': 'moderate','1': 'wet', '2': 'dry'}
    wyt = mapping_dict[wyt_encoded]
    
    return wyt


def remove_offset_from_julian_date(julian_offset_date, julian_start_date):
    """offset date counts 0 for start date. Converted to use 0 for 1/1"""
    if bool(not julian_offset_date or np.isnan(julian_offset_date)) and julian_offset_date != 0:
        julian_nonoffset_date = np.nan
    elif julian_offset_date < 366 - julian_start_date:
        julian_nonoffset_date = julian_offset_date + julian_start_date
    else:
        julian_nonoffset_date = julian_offset_date - (365 - julian_start_date)
    return julian_nonoffset_date