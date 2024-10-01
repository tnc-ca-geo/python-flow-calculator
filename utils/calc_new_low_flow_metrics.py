import numpy as np 
from datetime import datetime, timedelta
import calendar
# Set the window size for the rolling average (change this if in the future the window is meant to be shrunk or expanded)
window_size = 7

def longest_consecutive_count(data_slice, threshold=0.1):
    max_count = 0
    count = 0
    for val in data_slice:
        if val <= threshold:
            count += 1
            if count > max_count:
                max_count = count
        else:
            count = 0
    return max_count

def first_zero(data_slice, invalid_val=np.nan):
    for idx, val in enumerate(data_slice):
        if val <= 0.1:
            return idx
    return invalid_val

def calc_new_low_flow_metrics(flow_matrix, start_year, start_indices_array):
    num_cols = flow_matrix.shape[1]
    # Initialize lists to store metrics
    zeros_per_year = []
    classification_list = []
    first_zero_indices = []
    min_values = []
    min_indices = []
    start_dates_array_clean = np.array(start_indices_array, dtype=float)
    start_dates_array_clean = np.nan_to_num(start_dates_array_clean, nan=152)
    start_dates_array_clean = start_dates_array_clean.astype(int)

    for col in range(num_cols - 1):
        Y = start_year + col
        
        # Stack the current column with the next column
        current_column = flow_matrix[:, col]
        next_column = flow_matrix[:, col + 1]
        
        if Y % 4 == 0 and (Y % 400 == 0 or Y % 100 != 0) == True:
            stacked_cols = np.concatenate((current_column, next_column), axis=0)
        else:
            stacked_cols = np.concatenate((current_column[:-1], next_column), axis=0)
        total_days = len(stacked_cols)
        
        # Generate dates corresponding to the stacked data
        start_date_oct1 = datetime(Y, 10, 1)
        dates = np.array([start_date_oct1 + timedelta(days=i) for i in range(total_days)])
        
        start_index = start_dates_array_clean[col] - 1
        date_start = dates[start_index]
        date_end = datetime(date_start.year, 12, 31)
        days_to_dec31 = (date_end - date_start).days + 1  # + 1 to include Dec 31
        end_index = start_index + days_to_dec31
        end_index = min(end_index, total_days)
        
        # Extract the data
        data_slice = stacked_cols[start_index:end_index]
        # Now process metrics for this year's dry season
        # no data = no metrics
        if np.count_nonzero(~np.isnan(data_slice)) < np.count_nonzero(np.isnan(data_slice)):
            classification_list.append(None)
            first_zero_indices.append(None)
            min_values.append(None)
            min_indices.append(None)
            zeros_per_year.append(None)
            continue
        
        # Metric 1: Classification based on longest consecutive zero flow days
        consecutive_low_flow = longest_consecutive_count(data_slice, threshold=0.1)

        is_intermittent = consecutive_low_flow >= 5
        classification = 'Intermittent' if is_intermittent else 'Perennial'
        classification_list.append(classification)
        
        # Metric 2: First zero flow day
        first_zero_idx = first_zero(data_slice, invalid_val=None)
        if first_zero_idx is not None:
            first_zero_idx = first_zero_idx + start_index + 1
        first_zero_indices.append(first_zero_idx)
        
        # Metric 3: Number of zero flow days
        # Dont calculate for Perennial years, will probably be low and the 7-day metrics are much better
        if not is_intermittent:
            zeros = None
        else: 
            zeros = np.sum(data_slice <= 0.1)
        zeros_per_year.append(zeros)

        # Metric 4 & 5: Minimum rolling 7-day average and its occurrence index
        # Dont calculate for Intermittent years (will probably just be 0)
        if is_intermittent:
            min_value = None
            min_index = None
        elif len(data_slice) >= window_size:
            rolling_avg = np.convolve(data_slice, np.ones(window_size)/window_size, mode='valid')
            min_value = np.nanmin(rolling_avg)
            min_index = np.nanargmin(rolling_avg)
            if min_index is not None:
                min_index = min_index + start_index + 1
            else:
                min_value = None
                min_index = None
        min_values.append(min_value)
        min_indices.append(min_index)
        
    # Metric 6: Overall classification
    num_intermittent = sum(1 for c in classification_list if c == 'Intermittent')
    num_perennial = sum(1 for c in classification_list if c == 'Perennial')
    total_sum = num_intermittent + num_perennial
    if total_sum == 0:
        classification_overall = ''
    else:
        percentage_intermittent = (num_intermittent / total_sum) * 100
        classification_overall = 'Intermittent' if percentage_intermittent > 15 else 'Perennial'
    

    return min_values, min_indices, classification_overall, zeros_per_year, first_zero_indices, classification_list