import numpy as np
from utils.helpers import replace_nan, regex_peak_detection
from params import flashy_params

def Altered_Fall_Wet_Timing(flow_matrix, DS_Tim):
    np.set_printoptions(suppress=True)
    # Setup the output vectors
    FA_Tim = []
    Wet_Tim = []
    FA_Mag = []
    FA_Dur = []
    FA_Dif_num = []
    Temp_Wet_Tim = []
    Temp_DS_flow = []
    # fall peak
    min_height = flashy_params['fall_min_height']
    
    # wet peak
    min_peak_height = flashy_params['wet_min_peak_height']
    min_peak_scaling_factor = flashy_params['wet_min_peak_scaling_factor']

    # general
    median_scaling_factor = flashy_params['fall_median_scaling_factor']
    max_nan_per_year = flashy_params['max_nan_allowed_per_year']
    max_zero_per_year = flashy_params['max_zero_allowed_per_year']

    # Loop through all of the water years
    for column_number in range(flow_matrix.shape[1]):
        wet_tim_len = len(Wet_Tim)
        # Filter the flow data to the individual water year
        flow_data = flow_matrix[:, column_number]
        
        if column_number == 0:
            FA_Tim.append(np.nan)
            FA_Mag.append(np.nan)
            FA_Dif_num.append(np.nan)
            FA_Dur.append(np.nan)
            Wet_Tim.append(np.nan)
            continue
        
        # Skip the year if there are more than 100 NA flow data points
        if (np.count_nonzero(np.isnan(flow_data)) >= max_nan_per_year  or
            np.all(flow_data < 1)):
            # If conditions are met, set all the metrics to NaN
            FA_Tim.append(np.nan)
            FA_Mag.append(np.nan)
            FA_Dif_num.append(np.nan)
            FA_Dur.append(np.nan)
            Wet_Tim.append(np.nan)
            continue

        # Check to see if there are more than the allowable number of 0s in the vector
        elif np.sum((flow_data <= 0.1) & ~np.isnan(flow_data)) >= max_zero_per_year:
            FA_Tim.append(np.nan)
            FA_Mag.append(np.nan)
            FA_Dif_num.append(np.nan)
            FA_Dur.append(np.nan)
            Wet_Tim.append(np.nan)
            continue

        # Check to see if this is a flat lined year
        elif np.all(~np.isnan(flow_data) & (flow_data == flow_data[~np.isnan(flow_data)][0])):
            FA_Tim.append(np.nan)
            FA_Mag.append(np.nan)
            FA_Dif_num.append(np.nan)
            FA_Dur.append(np.nan)
            Wet_Tim.append(np.nan)
            continue
        
        current_year = flow_matrix[:, column_number].T
        
        previous_year = flow_matrix[:, column_number-1].T
        WY_start = len(previous_year) + 1

        flow_data = np.concatenate((previous_year, current_year), axis=0)
        flow_data = replace_nan(flow_data.copy())

        WY_median = np.median(flow_data)
        FA_Check = False

        flow_window = flow_data[WY_start-1:(WY_start + 75)]

        min_height = min((0.15*WY_median),min_height)
        FA_peaks = regex_peak_detection(flow_window, peakpat = "[+]{1,}[0]{,40}[-]{1,}", threshold = min_height)

        if FA_peaks is not None and len(FA_peaks) > 0:
            # Loop through the peaks

            for j in range(len(FA_peaks)):
                # See if the last peak met the criteria
                if FA_Check:
                    # If so, break the loop
                    break
                
                if (not np.isnan(DS_Tim[column_number-1])) and DS_Tim[column_number-1] > 0:
                    Temp_DS_flow = flow_data[DS_Tim[column_number-1]:(FA_peaks[j, 1].astype(int) + WY_start)]
                    Temp_DS_Mag = np.median(Temp_DS_flow)
                elif np.isnan(DS_Tim[column_number-1]) or DS_Tim[column_number-1] < 0:
                    Temp_DS_flow = flow_data[0:(FA_peaks[j, 1] + WY_start).astype(int)]
                    Temp_DS_Mag = np.median(Temp_DS_flow)

                # To check if the fall pulse meets certain criteria
                if FA_peaks[j, 0] > median_scaling_factor * Temp_DS_Mag and FA_peaks[j, 0] >= 1:

                    # Store the identified timing for the fall pulse
                    FA_Tim_Temp = FA_peaks[j, 1]
                    FA_Dur_Temp = FA_peaks[j, 3] - FA_peaks[j, 2]
                    FA_Mag_Temp = FA_peaks[j, 0]

                    # Look for the start of the wet season to check if the fall peak actually qualifies
                    post_fall_flow = flow_data[(FA_Tim_Temp + FA_Dur_Temp + WY_start).astype(int):]
                    # Calculate the rolling median of flows post fall
                    median_array = np.array([np.median(post_fall_flow[:i+1]) for i in range(len(post_fall_flow))])
                    # Find the index of the first flow that is 1.5 times the median
                    wet_tim = np.where(post_fall_flow > median_scaling_factor * median_array)

                    if not (wet_tim[0].size == 0):
                        Temp_Wet_Tim = np.where(post_fall_flow > median_scaling_factor * median_array)[0][0]
                    else:
                        Temp_Wet_Tim = None
                    # To get the dry season median, make sure there was a dry season timing next year
                    if not np.isnan(DS_Tim[column_number-1]) and DS_Tim[column_number-1] < 0 and Temp_Wet_Tim is not None:

                        # Calculate the potential dry season 50th percentile flow
                        Temp_DS_Mag = np.median(flow_data[DS_Tim[column_number-1]:(FA_Tim_Temp + FA_Dur_Temp + Temp_Wet_Tim + WY_start).astype(int)])

                    # If there wasn't a dry season timing, then look at the entire flow array
                    elif (np.isnan(DS_Tim[column_number-1]) or DS_Tim[column_number-1] < 0) and Temp_Wet_Tim is not None:

                        # Calculate the potential dry season 50th percentile flow
                        Temp_DS_Mag = np.median(flow_data[0:(FA_Tim_Temp + FA_Dur_Temp + Temp_Wet_Tim + WY_start).astype(int)])
                    # Check if the fall pulse is still 1.5 times the dry season 50th percentile flow
                    if FA_Mag_Temp > median_scaling_factor * Temp_DS_Mag:
                        FA_Tim.append((FA_peaks[j, 1] +1).astype('int'))
                        if Temp_Wet_Tim is None:
                            Wet_Tim.append(None)
                        else:
                            Wet_Tim.append((FA_peaks[j, 1] + FA_Dur_Temp + Temp_Wet_Tim).astype('int'))
                        FA_Mag.append(FA_peaks[j,0])
                        FA_Dif_num.append(FA_peaks[j,0]-Temp_DS_Mag)
                        FA_Dur.append(FA_peaks[j,1] - FA_peaks[j,2])
                        FA_Check = True
                        break
                    else:
                        continue  

            if not FA_Check:
                FA_Tim.append(np.nan)
                FA_Mag.append(np.nan)
                FA_Dif_num.append(np.max(FA_peaks[:,0]) - Temp_DS_Mag)
                FA_Dur.append(np.nan)
                
        else:
            FA_Tim.append(np.nan)
            FA_Mag.append(np.nan)
            FA_Dif_num.append(0)
            FA_Dur.append(np.nan)

        if not FA_Check:
            # If there was no fall pulse then find the first pulse after that is 1.5 Dry season baseflow after the fall pulse period
            # first get the flow data from after the fall pulse window
            Wet_Peaks_flow = flow_data[WY_start + 75:]
            # Now find the peaks after in the post fall window

            WS_peaks = regex_peak_detection(Wet_Peaks_flow, peakpat = "[+]{1,}[0]{,5}[-]{1,}",threshold =min((min_peak_scaling_factor*WY_median),min_peak_height))
            # Check to make sure there is data in the output from the peaks analysis
            if len(WS_peaks) > 0:
                # Loop through the peaks to see if there is a qualifying peak
                for j in range(len(WS_peaks)):
                    # Check to see if the peaks meet 1.5 times the baseline threshold
                    # First make a vector of the flow values from the previous dry season until the potential peak

                    # To do this we need to make sure that there was a previous dry season timing
                    # To get the dry season median we need to make sure there was a dry season timing next year
                    if (not np.isnan(DS_Tim[column_number - 1])) and DS_Tim[column_number - 1] > 0:
                        # Calculate the potential dry season 50th percentile flow
                        Temp_DS_flow = flow_data[DS_Tim[column_number - 1]:(WS_peaks[j, 1] + WY_start).astype(int)]
                        Temp_DS_Mag = np.median(Temp_DS_flow)
                
                    elif np.isnan(DS_Tim[column_number - 1]) or DS_Tim[column_number - 1] < 0:
                        # Calculate the potential dry season 50th percentile flow
                        Temp_DS_flow = flow_data[0:(WS_peaks[j, 2] + WY_start).astype(int)]
                        Temp_DS_Mag = np.median(Temp_DS_flow)
                        
                    # Check to see if the peak is larger than the estimated dry season baseflow
                    if WS_peaks[j, 0] > median_scaling_factor * Temp_DS_Mag:
                        # Now we know we either have a peak on or peak before a "hat" scenario,
                        # so we need to check the timing of the peak

                        # To do that we are first going to 90th percentile flow for the current flow year
                        current_flowyear = flow_data[WY_start+1:]

                        threshold_90 = np.quantile(current_flowyear, 0.9)

                        # Find subset of data above the 90th percentile or above 1 cfs if the 90th percentile is less than
                        flow_90th = Wet_Peaks_flow[Wet_Peaks_flow >= max(threshold_90, 1)]
                        # If all of the flows are less than 1 cfs then just use the 90th percentile flow
                        if len(flow_90th) < 1:
                            flow_90th = Wet_Peaks_flow[ Wet_Peaks_flow >= threshold_90]

                        # find the first day that is at or above the 90th percentile of flow and the last date to check
                        Wet_start_index_1 = np.where(Wet_Peaks_flow >= max(threshold_90, 1))[0][0]
                        index_1_check = np.where(Wet_Peaks_flow >= max(threshold_90, 1))[0][-1]

                        # Then get the index of the start of the qualified peak
                        Wet_start_index_2 = int(WS_peaks[j, 2])

                        # Check to see which potential timing
                        if index_1_check < Wet_start_index_2:
                            # if the first index is smaller then set that as the wet season
                            Wet_Tim.append(Wet_start_index_1 + 75)
                        elif index_1_check >= Wet_start_index_2:
                            # Set the wet season start timing
                            Wet_Tim.append(75 + Wet_start_index_2)

                        break

                # If all peaks are below the 90th flow percentile then we will just choose the day before the 1st day of 90th flow
                # If none of the post fall pulse peaks meet the criteria it is likely a peak prior to a hat scenario
                # and we want to find the last day before the 90th percentile flow of that flow year
                Temp_dry_flow = flow_matrix[:, column_number]
                Temp_dry_flow = replace_nan(Temp_dry_flow)
                threshold_90 = np.quantile(Temp_dry_flow, 0.9)

                if all(WS_peaks[:, 0] < median_scaling_factor * Temp_DS_Mag) or len(WS_peaks) <= 0:
                    # Find subset of data above the 90th percentile
                    flow_90th = Temp_dry_flow[Temp_dry_flow >= threshold_90]
                    # find the first day that is at or above the 90th percentile of flow
                    start_date = flow_90th[0]
                    
                    # then go one day back to capture the rising limb
                    Wet_start_index = np.where(Temp_dry_flow == start_date)[0][0] - 1

                    # Set the wet season timing to that date
                    Wet_Tim.append(Wet_start_index)

            else:
                # If there aren't any peaks then it is likely a hat scenario
                # and we want to find the last day before the 90th percentile flow of that flow year
                Temp_dry_flow = flow_matrix[:, column_number]
                Temp_dry_flow = replace_nan(Temp_dry_flow)

                if (not np.isnan(DS_Tim[column_number - 1])) and DS_Tim[column_number - 1] > 0:
                    # Calculate the potential dry season 50th percentile flow
                    Temp_DS_flow = flow_data[DS_Tim[column_number - 1]:]
                    Temp_DS_Mag = np.median(Temp_DS_flow)
                elif (np.isnan(DS_Tim[column_number - 1]) or DS_Tim[column_number - 1] < 0) and len(WS_peaks) > 0:
                    # Calculate the potential dry season 50th percentile flow
                    Temp_DS_flow = flow_data[0:(WS_peaks[-1, 2] + WY_start)]
                    Temp_DS_Mag = np.median(Temp_DS_flow)
                else:
                    Temp_DS_flow = flow_data
                    Temp_DS_Mag = np.median(Temp_DS_flow)

                threshold_90 = np.quantile(Temp_dry_flow, 0.9)
                if all(WS_peaks[:, 0] < median_scaling_factor * Temp_DS_Mag) or len(WS_peaks) <= 0:
                    # Find subset of data above the 90th percentile
                    flow_90th = Temp_dry_flow[(Temp_dry_flow >= threshold_90 ) & (Temp_dry_flow > 0)]
                    # find the first day that is at or above the 90th percentile of flow
                    start_date = flow_90th[0]
                    # then go one day back to capture the rising limb
                    Wet_start_index = np.where(Temp_dry_flow == start_date)[0][0] - 1

                    # Set the wet season timing to that date
                    Wet_Tim.append(Wet_start_index)
                    
        # The calculator has failed to assign a wet timing this iteration, give it nan
        if wet_tim_len == len(Wet_Tim):
            Wet_Tim.append(np.nan)


    # Put all the metrics into a dictionary
    Fall_Metrics_and_Wet_tim = {
    "timings_water": FA_Tim,
    "magnitudes": FA_Mag,
    "durations": FA_Dur,
    #"FA_Dif_num": FA_Dif_num,
    "Wet_Tim": Wet_Tim
    }
    
    # Return all of the metrics
    return Fall_Metrics_and_Wet_tim
