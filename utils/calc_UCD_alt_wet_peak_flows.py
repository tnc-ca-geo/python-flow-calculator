import numpy as np
from scipy.stats import norm
from utils.helpers import replace_nan
from params import flashy_params

def median_of_time(lt):
    n = len(lt)
    if n < 1:
        return None
    elif n % 2 == 1:
        return lt[n % 2]
    elif n == 2:
        first_date = lt[0]
        second_date = lt[1]
        return (first_date + second_date) / 2
    else:
        first_date = lt[n % 2 - 1]
        second_date = lt[n % 2]
        return (first_date + second_date) / 2

def peak_flow_analysis(peaks, average_return_interval):
    # First rank the provided peaks
    ranked_peaks = np.sort(peaks)[::-1]

    # Assign ranks to each flow
    ranks = np.arange(1, len(ranked_peaks) + 1)
    
    # Take the log of all the peak flows
    log_ranked_peaks = np.log(ranked_peaks)
    
    # Get the mean of the peaks
    average_peak = np.nanmean(ranked_peaks)

    # This gets the mean of the log peaks
    log_average_peak = np.nanmean(log_ranked_peaks)

    # Now calculate the squared mean difference of the log flows
    log_sqr_mean_diff = (log_ranked_peaks - log_average_peak)**2

    # And the cubed average difference of the log flows
    log_cbd_mean_diff = (log_ranked_peaks - log_average_peak)**3

    # Now calculate the return period for ranked peak
    return_int = (len(ranks) + 1) / ranks

    # Convert that into exceedance probability
    e_p = 1 / return_int

    # Calculate the variance
    variance = np.nansum(log_sqr_mean_diff) / (len(ranked_peaks) - 1)
    
    # Calculate the Standard Deviation
    sd = np.sqrt(variance)
    
    # Calculate the skew
    skew = (len(peaks) * np.nansum(log_cbd_mean_diff)) / ((len(peaks) - 1) * (len(peaks) - 2) * sd**3)

    z_score = norm.ppf(1 - 1 / average_return_interval)

    # Calculate the K
    kp = (2 / skew) * (1 + skew * z_score / 6 - skew**2 / 36)**3 - 2 / skew

    # Calculate the return flow in log space
    log_return_q = log_average_peak + kp * sd

    # Take the calculated return flow back to normal space
    return_flow = np.exp(log_return_q)
    # Now we need to adjust the skew for weighting
    # First the regional skewness, this comes from figure Cr < 0.2
    # Second the variance of regional skewness, from Parrett et al. 2011
    # "Regional skew for California, and flood frequency for selected sites...
    # in the Sacramento–San Joaquin River Basin..."
    # The average value in the study was used
    # V_Cm = 0.364

    return return_flow


def calc_winter_highflow_annual_combined(flow_matrix, original_method=False):

    max_zero_allowed_per_year = flashy_params['max_zero_allowed_per_year']
    max_nan_allowed_per_year = flashy_params['max_nan_allowed_per_year']

    # Set up output arrays
    peak_dur_10 = []
    peak_dur_2 = []
    peak_dur_5 = []
    peak_10 = []
    peak_2 = []
    peak_5 = []
    peak_fre_10 = []
    peak_fre_2 = []
    peak_fre_5 = []
    peak_tim_10 = []
    peak_tim_2 = []
    peak_tim_5 = []

    # Define average recurrence interval
    recurrence_intervals = [2, 5, 10]
    peak_flows = []


    # Cycle through the years to determine the peak flows each year that has data
    for column_number in range(flow_matrix.shape[1]):
        # Filters flow to the water year of interest
        flow_data = flow_matrix[:, column_number]
        if (np.count_nonzero(np.isnan(flow_data)) >= max_nan_allowed_per_year  or
            np.all(flow_data < 1)):
            continue
        
        peak_flows.append(np.max(flow_matrix[:, column_number]))
    # Array for the return flow thresholds
    peak_exceedance_values = []

    # Run through each recurrence interval and determine flow threshold for each
    for ari in recurrence_intervals:
        # This mode follows the original calculator
        if original_method:
            peak_exceedance_values.append(np.quantile(peak_flows, 1 - (1 / ari)))
        else:
            # This method uses Log Pearson Type III method to calculate the return flows
            peak_exceedance_values.append(peak_flow_analysis(peak_flows, ari))

    # Now iterate through the water years to see when these flows occur
    for column_number in range(flow_matrix.shape[1]):
        flow_data = flow_matrix[:, column_number]

        # Check to make sure that flow years qualify for the analysis
        if ( np.sum(np.isnan(flow_data)) > max_nan_allowed_per_year or
                 np.sum((flow_data <= 0.1)) > max_zero_allowed_per_year or
                len(flow_data) <= 358):
            # Set all the values to NA besides the peak flow thresholds
            peak_dur_10.append(np.nan)
            peak_dur_2.append(np.nan)
            peak_dur_5.append(np.nan)
            peak_10.append(peak_exceedance_values[2])
            peak_2.append(peak_exceedance_values[0])
            peak_5.append(peak_exceedance_values[1])
            peak_fre_10.append(np.nan)
            peak_fre_2.append(np.nan)
            peak_fre_5.append(np.nan)
            peak_tim_10.append(np.nan)
            peak_tim_2.append(np.nan)
            peak_tim_5.append(np.nan)
            continue

        # Now that the data has passed the checks, replace the NA data
        flow_data = replace_nan(flow_data.copy())

        # If the year does qualify, iterate through exceed values
        for j, exceed_value in enumerate(peak_exceedance_values):
            # Determine which flows qualify
            qual_flows = np.where(flow_data >= exceed_value, 1, 0)
            # The duration is calculated by summing the number of days that qualify
            ph_dur = np.nansum(qual_flows)
            if ph_dur < 1:
                ph_dur = np.nan

            # Now we determine the median timing
            # first we determine where it transitions from false to true
            transitions = np.concatenate(([False], np.diff(qual_flows) == 1))

            timings = np.where(transitions)[0]
            
            # Find the median start timing
            ph_tim = np.median(timings) if len(timings) > 0 else np.nan

            # Find the number of times that the flow crossed the exceed threshold values
            #qualified_flows = np.split(qual_flows, np.where(np.diff(qual_flows) != 0)[0])
            #ph_fre = sum(len(qf) > 1 for qf in qualified_flows)
            transition_indices = np.where(np.diff(qual_flows) == 1)[0]
            ph_fre = len(transition_indices)
            if ph_fre < 1:
                ph_fre = np.nan

            if j == 0:
                peak_dur_2.append(ph_dur)
                peak_2.append(peak_exceedance_values[0])
                peak_fre_2.append(ph_fre)
                peak_tim_2.append(ph_tim)
            elif j == 1:
                peak_dur_5.append(ph_dur)
                peak_5.append(peak_exceedance_values[1])
                peak_fre_5.append(ph_fre)
                peak_tim_5.append(ph_tim)
            elif j == 2:
                peak_dur_10.append(ph_dur)
                peak_10.append(peak_exceedance_values[2])
                peak_fre_10.append(ph_fre)
                peak_tim_10.append(ph_tim)
    
    # the names below are a bit weird because the reference calculator used exceedance percentiles instead of recurrence intervals
    high_flow_metrics = {
        "durations_ten": peak_dur_10,
        "durations_fifty": peak_dur_2,
        "durations_twenty": peak_dur_5,
        "magnitudes_ten": peak_10,
        "magnitudes_fifty": peak_2,
        "magnitudes_twenty": peak_5,
        "frequencys_ten": peak_fre_10,
        "frequencys_fifty": peak_fre_2,
        "frequencys_twenty": peak_fre_5,
        "timings_ten": peak_tim_10,
        "timings_fifty": peak_tim_2,
        "timings_twenty": peak_tim_5
    }

    return high_flow_metrics