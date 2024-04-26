import numpy as np 
from datetime import datetime

# Set the window size for the rolling average (change this if in the future the window is meant to be shrinked or expanded)
window_size = 7

def longest_consecutive_count(arr, threshold=0.1):
    below_threshold = (arr <= threshold)
    count_per_column = np.zeros(arr.shape[1], dtype=int)

    for col in range(arr.shape[1]):
        current_count = 0
        max_count = 0

        for value in below_threshold[:, col]:
            if value:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        count_per_column[col] = max_count

    return count_per_column

def first_zero(arr, axis, invalid_val=-1):
    mask = arr <= 0.1
    res = np.where(mask.any(axis=axis), mask.argmax(axis=axis), invalid_val)
    mask = (res != 0) & (~np.isnan(res))
    res[mask]
    return res
    
def calc_new_low_flow_metrics(flow_matrix, start_year, start_date):
    
    # First step is to refactor the data to be looking at the window from june 1 to jan 30, this is trickier then you would think because of the way the data is expressed 
    # using a fake year to compare the dates
    june_1 = datetime.strptime('2023/06/01','%Y/%m/%d')
    current_start_time = datetime.strptime('2023/' + start_date, '%Y/%m/%d')
    if current_start_time > june_1:
        june_1 = datetime.strptime('2024/06/01','%Y/%m/%d')
    
    delta =  current_start_time - june_1
    
    # initialization 
    adjusted_matrix = np.copy(flow_matrix)
    num_cols = adjusted_matrix.shape[1]
    result = []

    # Iterate over each column except the last one
    for col in range(num_cols - 1):
        # Stack the current column with the next column
        column = adjusted_matrix[:, col]
        column = column.reshape(-1, 1)
        next_column = adjusted_matrix[:, col + 1]
        next_column = next_column.reshape(-1, 1)
        stacked_cols = np.concatenate((column, next_column), axis=0)
        result.append(stacked_cols)
    # numpy 2-d array of each column and its next one stacked meaning each column represents the current water year and the next
    result = np.concatenate(result, axis = 1)
    # now that columns are stacked roll them back along each column so that index 0 is june 1
    result = np.roll(result, delta.days + 1, axis = 0)
    # adjust leap years
    offset = start_year % 4
    for j in range(num_cols - 1):
        column = result[:, j]
        if ((j + offset) % 4 == 0):
            result[:, j] = np.roll(column, -1)
            
    # limit to the first 243 elements (from june 1 to jan 30)
    adjusted_matrix = result[:243, :]
    
    # METRIC 1 number of 0 flow days
    zeros_per_year = np.sum(adjusted_matrix <= 0.1, axis=0)
    
    # METRIC 2 Classification:
    # Get longest consecutive streak of no flow days
    consecutive_low_flow = longest_consecutive_count(adjusted_matrix, threshold=0.1)
    #check if each year is above 5
    classification_arr = (consecutive_low_flow >= 5)
    num_intermittent = np.sum(classification_arr)
    # Calculate the percentage of Intermittent years
    percentage_Intermittent = (num_intermittent / len(classification_arr)) * 100
    # if the percentage is > 15% then the overall classification is intermittent otherwise it is perennial
    classification_overall = 'Perennial'
    if percentage_Intermittent > 15:
        classification_overall = 'Intermittent'
    #reformat the array from true false to intermittent and perennial
    classification_arr = np.where(classification_arr, 'Intermittent', 'Perennial')

    # METRIC 3: first zero flow day
    # Find the indices of the first zero for each year
    first_zero_indices = first_zero(adjusted_matrix, axis = 0, invalid_val=np.nan)

    # METRIC 4 & 5: min rolling 7 day avg and the date it occurs at
    # Calculate the rolling average along the row
    weights = np.ones(window_size) / window_size
    rolling_avg = np.apply_along_axis(lambda x: np.convolve(x, weights, mode='valid'), axis=0, arr=adjusted_matrix)
    # Find the minimum value and its index along each column (propogating all nan columns)
    min_values = np.nanmin(rolling_avg, axis= 0)

    min_indices = []
    for i, value in enumerate(min_values):
        
        column = rolling_avg[:, i] 
        matches = np.where(column == value)[0]
        
        if matches.size > 0: # Check if a match is found
            min_indices.append(matches[0])
        else:
            min_indices.append(np.nan)

    return min_values, min_indices, classification_overall, zeros_per_year, first_zero_indices, classification_arr