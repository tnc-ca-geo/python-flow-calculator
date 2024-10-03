import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
import re
from numpy import NaN, Inf, arange, isscalar, asarray, array
from utils.constants import TYPES

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
    current_count = 0
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

def calc_avg_nan_per_year(results):
    dataset = []
    dict_to_array(results['wet'], 'wet', dataset)
    dict_to_array(results['spring'], 'spring', dataset)
    dict_to_array(results['summer'], 'summer', dataset)
    df = pd.DataFrame(dataset)
    df.dropna(axis = 1, how = 'all',inplace = True)
    total_nan = df.isnull().sum().sum()
    num_years = len(df.columns) - 1
    return(total_nan/num_years)

def remove_offset_from_julian_date(julian_offset_date, julian_start_date):
    """offset date counts 0 for start date. Converted to use 0 for 1/1"""
    if bool(not julian_offset_date or np.isnan(julian_offset_date)) and julian_offset_date != 0:
        julian_nonoffset_date = np.nan
    elif julian_offset_date < 366 - julian_start_date:
        julian_nonoffset_date = julian_offset_date + julian_start_date
    else:
        julian_nonoffset_date = julian_offset_date - (365 - julian_start_date)
    return julian_nonoffset_date

def dict_to_array(data, field_type, dataset):
    for key, value in data.items():
        if field_type == 'winter':
            try:
                for k, v in value.items():
                    if key.find('timings') > -1:
                        continue
                    data = v
                    # remove two and five percentiles from output
                    if k.find('two') > -1 or k.find('five') > -1:
                        continue
                    else:
                        if k.find('_water') > -1:
                            tmp = k.split('_water')[0]
                            data.insert(
                                0, TYPES[field_type+'_'+key+'_'+str(tmp)] + '_water')
                        else:
                            data.insert(0, TYPES[field_type+'_'+key+'_'+str(k)])
                        dataset.append(data)
            except AttributeError as e:
                data = value
                data.insert(0, TYPES[field_type+'_'+key])
                dataset.append(data)
                
        elif field_type == '':
            # dont add a leading underscore for no reason
            data = value
            data.insert(0, TYPES[key])
            dataset.append(data)

        else:
            data = value
            data.insert(0, TYPES[field_type+'_'+key])
            dataset.append(data)

def regex_peak_detection(x, nups=1, ndowns=1, zero='0', peakpat=None,
               minpeakheight=float('-inf'), minpeakdistance=1,
               threshold=0, npeaks=0, sortstr=False):
    """
    Identifies peaks in a numeric vector x based on specified criteria.
    Made to mimic https://www.rdocumentation.org/packages/pracma/versions/1.9.9/topics/findpeaks within python
    Parameters:
        x (array-like): Numeric input vector.
        nups (int): Minimum number of consecutive increases.
        ndowns (int): Minimum number of consecutive decreases.
        zero (str): How to handle zeros in the diff sequence ('0', '+', or '-').
        peakpat (str): Custom regex pattern for peak detection.
        minpeakheight (float): Minimum height of peaks.
        minpeakdistance (int): Minimum distance between peaks.
        threshold (float): Minimum difference between peak and its surroundings.
        npeaks (int): Maximum number of peaks to return.
        sortstr (bool): Whether to sort peaks in descending order.

    Returns:
        numpy.ndarray: Array containing peak values and their positions, start and end.
    """
    x = np.asarray(x)
    if not np.issubdtype(x.dtype, np.number) or np.isnan(x).any():
        raise ValueError("Input 'x' must be a numeric vector without NaNs.")

    if zero not in ('0', '+', '-'):
        raise ValueError("Argument 'zero' can only be '0', '+', or '-'.")

    if ndowns is None:
        ndowns = nups

    # Compute the sign of the differences
    diffs = np.diff(x)
    signs = np.sign(diffs)
    signs_str_list = []
    for s in signs:
        if s > 0:
            signs_str_list.append('+')
        elif s < 0:
            signs_str_list.append('-')
        else:
            signs_str_list.append('0')
    sign_str = ''.join(signs_str_list)
    
    # Replace zeros if necessary
    if zero != '0':
        sign_str = sign_str.replace('0', zero)
    
          
    # Define the peak pattern
    if peakpat is None:
        peakpat = r'[+]{%d,}[-]{%d,}' % (nups, ndowns)

    # Find matches using regular expressions
    matches = list(re.finditer(peakpat, sign_str))
    if not matches:
        return np.array([])

    x1 = np.array([m.start() for m in matches])
    
    x2 = np.array([m.end() for m in matches])

    n = len(x1)
    xv = np.zeros(n)
    xp = np.zeros(n, dtype=int)

    # Find peak positions and values
    for i in range(n):
        xi = x1[i] + 1
        xj = x2[i] + 1
        segment = x[xi:xj]
        idx = np.argmax(segment)
        xp[i] = xi + idx
        xv[i] = x[xp[i]]

    # Apply height and threshold criteria
    x1_values = x[x1]

    x2_values = x[x2]
    pmax = np.maximum(x1_values, x2_values)

    condition = (xv >= minpeakheight) & ((xv - pmax) >= threshold)
    inds = np.where(condition)[-1]
    X = np.column_stack((xv[inds], xp[inds], x1[inds], x2[inds]))
    if minpeakdistance < 1:
        raise ValueError('Handling \'minpeakdistance < 1\' is logically not possible.')

    # Sort peaks if necessary
    if sortstr or minpeakdistance > 1:
        sl = np.argsort(-X[:, 0])
        X = X[sl]

    if X.size == 0:
        return np.array([])

    # Enforce minimum peak distance
    if minpeakdistance > 1:
        no_peaks = X.shape[0]
        badpeaks = np.zeros(no_peaks, dtype=bool)
        for i in range(no_peaks):
            ipos = X[i, 1]
            if not badpeaks[i]:
                dpos = np.abs(ipos - X[:, 1])
                mask = (dpos > 0) & (dpos < minpeakdistance)
                badpeaks = badpeaks | mask
        X = X[~badpeaks]

    # Limit the number of peaks if necessary
    if npeaks > 0 and npeaks < X.shape[0]:
        X = X[:npeaks]

    return X

def normalize(w):
    return w / np.sum(w)

def determine_window_length(x, window):
    if isinstance(window, (float, int)):
        if window < 1:
            return int(len(x) * window)
        else:
            return int(window)
    else:
        raise ValueError("window must be a numeric value")

def make_window(w, a):
    hw = abs(w / 2)
    e = np.exp(1)
    a = abs(a)
    ret = np.array([e ** (-0.5 * (a * (n - int(hw)) / hw) ** 2) for n in range(w)])
    return ret

def smth_gaussian(x, window=None, alpha=None, tails=False):
    """
    Apply Gaussian smoothing to a numeric vector x. That copys R's smth.gaussian
    """
    if x is None:
        raise ValueError("Numeric vector 'x' is required")
    if not isinstance(x, (list, np.ndarray)):
        raise ValueError("'x' must be a numeric vector")
    x = np.asarray(x, dtype=float)
    if alpha is None:
        raise ValueError("Parameter 'alpha' is required")
    if not isinstance(alpha, (float, int)):
        raise ValueError("'alpha' must be numeric")
    if window is None:
        raise ValueError("Parameter 'window' is required")

    window_length = determine_window_length(x, window)
    w = make_window(window_length, alpha)
    size_w = len(w)
    size_d = len(x)
    w = normalize(w)
    hkw_l = int(size_w / 2)
    hkw_r = size_w - hkw_l
    ret = np.zeros(size_d)
    
    for i in range(size_d):
        ix_d = np.arange(i - hkw_l, i + hkw_r)
        ix_w = (ix_d >= 0) & (ix_d < size_d)
        ix_d = ix_d[ix_w]
        W_nm = w[ix_w]
        if np.sum(ix_w) != size_w:
            W_nm = normalize(W_nm)
        D_nm = x[ix_d]
        ret[i] = np.dot(D_nm, W_nm)
    
    if not tails:
        ret[:hkw_l] = np.nan
        ret[-hkw_r:] = np.nan
    return ret