import numpy as np
from utils.helpers import drop_last_nan_columns, replace_nan, regex_peak_detection, smth_gaussian
from params import flashy_params

def Altered_Summer_Dry_Season_Tim_Varied(flow, flow_thresh, day_thresh=5, roc_thresh=0.02):

    roc = np.diff(flow) / flow[:-1]
    roc = np.insert(roc,0,np.nan)
    dif = np.diff(flow, prepend=np.nan)

    n_consec = 0
    n_neg = 0
    idx_consec = None
    idx_start = None
    DS_Tim = None

    for i in range(len(flow)):
        if i == 0:
            idx_start = i
            continue

        if idx_start is None:
            idx_start = i

        if (
            (np.abs(roc[i]) <= roc_thresh or (flow[i] < 50 and dif[i] <= 2))
            and flow[i] <= flow_thresh
            and idx_start is not None
        ):
            n_consec += 1
            if roc[i] < 0:
                n_neg += 1

            if n_consec == day_thresh:
                idx_consec = np.arange(idx_start, i + 1)
                break

        else:
            n_consec = 0
            n_neg = 0
            idx_start = None

    if idx_consec is None:
        if roc_thresh < 0.05:
            roc_thresh += 0.01
            DS_Tim = Altered_Summer_Dry_Season_Tim_Varied(
                flow=flow, flow_thresh=flow_thresh, day_thresh=day_thresh, roc_thresh=roc_thresh
            )
        elif roc_thresh > 0.045 and day_thresh >= 3:
            day_thresh -= 1
            DS_Tim = Altered_Summer_Dry_Season_Tim_Varied(
                flow=flow, flow_thresh=flow_thresh, day_thresh=day_thresh, roc_thresh=roc_thresh
            )
    if DS_Tim is None and idx_consec is None:
        return None
    
    if DS_Tim is None:
        if n_neg > 3:
            DS_Tim = idx_consec[-1]
        elif n_neg <= 3:
            DS_Tim = idx_consec[0]

    if DS_Tim is not None:
        if DS_Tim <= 0 and not np.isnan(DS_Tim):
            DS_Tim = 0 # 1 in the original code but accounts for indexing difference between R and python

    return int(DS_Tim) if DS_Tim is not None else None


def Altered_Spring_Recession(flow_matrix):
    np.set_printoptions(suppress=True)
    
    min_dry_flow_percent = flashy_params["dry_min_flow_percent"]
    max_nan_per_year = flashy_params["max_nan_allowed_per_year"]
    max_zero_per_year = flashy_params["max_zero_allowed_per_year"]
    min_peak_height = flashy_params["dry_min_peak_height"]
    min_peak_scaling_factor = flashy_params["dry_min_peak_scaling_factor"]
    window = flashy_params["dry_season_smoothing_window"]
    alpha = flashy_params["dry_season_smoothing_alpha"]

    # Setup the output vectors
    SP_Mag = []
    SP_Tim = []
    SP_ROC = []
    SP_ROC_Max = []
    SP_Dur = []
    DS_Tim = []
    flow_list = drop_last_nan_columns(flow_matrix)

    # Loop through all of the water years
    for column_number, flow_data_raw in enumerate(flow_list):
        # Filter the flow data to the individual water year
        flow_data = flow_data_raw

        # Skip the year if there are more than 100 NA flow data points
        if np.isnan(flow_data).sum() > max_nan_per_year:
            SP_Tim.append(np.nan)
            SP_Mag.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            DS_Tim.append(np.nan)
            continue

        # Check to see if there are more than the allowable number of 0s in the vector
        elif np.sum((flow_data <= 0.1) & ~np.isnan(flow_data)) >= max_zero_per_year:
            SP_Tim.append(np.nan)
            SP_Mag.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            DS_Tim.append(np.nan)
            continue

        # Check to see if this is a flat lined year
        elif np.all(~np.isnan(flow_data) & (flow_data == flow_data[~np.isnan(flow_data)][0])):
            SP_Tim.append(np.nan)
            SP_Mag.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            DS_Tim.append(np.nan)
            continue

        else:
            # Now that the data has passed the checks, replace the NA data
            flow_data = replace_nan(flow_data.copy())

            # Calculate the 50th and 90th percentile for the flows
            quants = np.quantile(flow_data, q=[0.5, 0.9])

            WY_median = np.median(flow_data)
            # Filter the flow to remove the noise on the rising limb
            filter_flow = smth_gaussian(flow_data, window=window, alpha= alpha, tails=True)
            # Returns array with indices for each peak and valley
            # do not add prominence here, better matches the R code without it
            # max of 3 flat top points to match R code
            threshold = min((min_peak_scaling_factor*WY_median),min_peak_height)
            peaks = regex_peak_detection(filter_flow, peakpat = "[+]{1,}[-]{1,}")
            peaks_2 = regex_peak_detection(filter_flow, peakpat = "[+]{1,}[0]{1,30}[-]{1,}")
            # Combine the two data sets of peaks
            if peaks_2.any() and peaks.any():
                peaks_all = np.vstack((peaks, peaks_2))
            elif peaks_2.any():
                # above failed but this did not so peaks_2 has data but peaks does not
                peaks_all = peaks_2
            else:
                # both above cases failed so default to peaks, if it is empty that will be handled later
                peaks_all = peaks

            # Check to make sure there is data in the peaks
            if peaks_all.any():
                # If there is data in the data frame, then make sure it is more than just the titles
                if peaks_all.shape[0] > 0:
                    # Filter out peaks that are not above the 90th percentile and peaks that are in September
                    
                    peaks_all = peaks_all[peaks_all[:, 1].argsort()]
                   
                    peaks_90 = peaks_all[(peaks_all[:, 0] > quants[1]) & (peaks_all[:, 1] < 344)]
                else:
                    peaks_90 = None

            else:
                peaks_90 = None

            # Check to make sure that there are qualified peaks
            if peaks_90 is not None and peaks_90.shape[0] > 0:
                # Assign the last peak of the year as the first potential spring timing
                PH1_start = peaks_90[-1,1]
                PH1_poten = np.arange(PH1_start - 2, PH1_start + 3).astype(np.int64)
                max_flow = np.max(flow_data[PH1_poten])
                max_flow_check = np.where(flow_data[PH1_poten] == max_flow)[0][-1]
                springindex_PH1 = int(peaks_90[-1, 1]) - 3 + max_flow_check
                if (springindex_PH1 <= 75) and (len(peaks_90) < 2):
                    # springindex_PH1 = None
                    # this line is commented out in the original code and this block is empty
                    pass
            else:
                springindex_PH1 = None

            # Find the index of flows at or above the 90th percentile
            highflows = np.where(flow_data >= quants[1])

            # Assign the last index above 90th percentile flow as the second potential spring recession index
            springindex_PH2 = np.max(highflows)

            # If the first placeholder is not valid, then use the second placeholder value
            if springindex_PH1 is None:
                # Set the index of the spring timing to the second placeholder
                springindex = springindex_PH2
            else:
                # Otherwise, set the spring index to the first placement
                springindex = springindex_PH1 + 1

            if springindex > 364:
                # dont allow spring to start past the end of the water year but still add their magnitude?
                SP_Tim.append(None)
                SP_Mag.append(flow_data[springindex])
            else:
                springIndexAdjusted = springindex + 1
                SP_Tim.append(springIndexAdjusted)
                SP_Mag.append(flow_data[springindex])

        # Make a new data frame with just the flows after the top of the spring recession
        flow_post_SP = flow_data[springindex:]


        WY_max_flow = np.max(flow_data)
        post_SP_min_flow = np.min(flow_post_SP)
        Min_DS_Threshold = post_SP_min_flow + (WY_max_flow - post_SP_min_flow) * min_dry_flow_percent

        # Calculate the dry season start timing by subtracting the length of the water year by the time remaining
        # after the spring recession peak and then add the timing of the start of the dry season after the spring peak
        PH_DS_Tim = Altered_Summer_Dry_Season_Tim_Varied(flow_post_SP, flow_thresh=Min_DS_Threshold)
        roc = np.diff(flow_post_SP) / flow_post_SP[:-1]
        roc = np.nan_to_num(roc, nan=0)
        roc = np.insert(roc, 0, np.nan)
        if PH_DS_Tim is None:
            DS_Tim.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            continue

        DS_Tim.append(PH_DS_Tim + springindex + 1)
        SP_Dur.append(PH_DS_Tim)
        SP_recs_temp = roc[1: 1 + SP_Dur[column_number]]
        SP_ROC.append( np.abs(np.median(SP_recs_temp[SP_recs_temp < 0])))
        if np.any(SP_recs_temp < 0):
            SP_ROC_Max.append(np.max(np.abs(SP_recs_temp[SP_recs_temp < 0])))
        else:
            # Handle the case when the array is empty
            SP_ROC_Max.append(0)
    # Put all the metrics into a dictionary
    SP_Metrics_and_Dry_Season_Tim = {
        "timings_water": SP_Tim,
        "magnitudes": SP_Mag,
        "rocs": SP_ROC,
        "durations": SP_Dur,
        # "SP_ROC_Max": SP_ROC_Max,
        "DS_Tim": DS_Tim
    }
    # Return all of the metrics
    return SP_Metrics_and_Dry_Season_Tim
