import numpy as np
from utils.helpers import replace_nan
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

def Altered_Summer_Dry_Season_Tim_Varied(flow, flow_thresh, day_thresh=5, roc_thresh=0.02):
    
    roc = np.diff(flow) / flow[:-1]
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

    if DS_Tim is None:
        if n_neg > 3:
            DS_Tim = idx_consec[-1]
        elif n_neg <= 3:
            DS_Tim = idx_consec[0]

    if DS_Tim is not None:
        if DS_Tim <= 0 and not np.isnan(DS_Tim):
            DS_Tim = 1

    return int(DS_Tim) if DS_Tim is not None else None


def Altered_Spring_Recession(flow_matrix):
    
    # Setup the output vectors
    SP_Mag = []
    SP_Tim_test = []
    SP_Tim = []
    SP_ROC = []
    SP_ROC_Max = []
    SP_Dur = []
    DS_Tim = []

    # Loop through all of the water years
    for column_number in range(flow_matrix.shape[1]):
        # Filter the flow data to the individual water year
        flow_data = flow_matrix[:, column_number]

        # Skip the year if there are more than 100 NA flow data points
        if np.isnan(flow_data).sum() > 100 or len(flow_data) < 358:
            SP_Tim.append(np.nan)
            SP_Mag.append(np.nan)
            SP_Tim_test.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            DS_Tim.append(np.nan)
            continue

        # Check to see if there are more than the allowable number of 0s in the vector
        elif np.sum((flow_data == 0) & ~np.isnan(flow_data)) >= 365:
            SP_Tim.append(np.nan)
            SP_Mag.append(np.nan)
            SP_Tim_test.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            DS_Tim.append(np.nan)
            continue

        # Check to see if this is a flat lined year
        elif np.all(~np.isnan(flow_data) & (flow_data == flow_data[~np.isnan(flow_data)][0])):
            SP_Tim.append(np.nan)
            SP_Mag.append(np.nan)
            SP_Tim_test.append(np.nan)
            SP_ROC.append(np.nan)
            SP_ROC_Max.append(np.nan)
            SP_Dur.append(np.nan)
            DS_Tim.append(np.nan)
            continue

        else:
            # Now that the data has passed the checks, replace the NA data
            flow_data = replace_nan(flow_data.copy())

            # Calculate the 50th and 9th percentile for the flows
            quants = np.percentile(flow_data, q=[50, 90], interpolation='nearest')

            WY_median = np.median(flow_data)
            # Filter the flow to remove the noise on the rising limb
            filter_flow = gaussian_filter1d(flow_data, 1.3)

            # Returns array with indicies for each peak and valley
            # do not add prominence here, better matches the R code without it
            # max of 3 flat top points to match R code
            peaks, valleys = find_peaks(filter_flow, height= min((0.15*WY_median),15), plateau_size=[0,3])

            values_at_peaks = filter_flow[peaks]
            # Combine the two data sets of peaks
            peaks_all = np.vstack((peaks, values_at_peaks)).T

            # Check to make sure there is data in the peaks
            if len(peaks_all) > 1:
                # If there is data in the data frame, then make sure it is more than just the titles
                if peaks_all.shape[0] > 0:
                    # Filter out peaks that are not above the 90th percentile and peaks that are in September
                    peaks_90 = peaks_all[(peaks_all[:, 1] > quants[1]) & (peaks_all[:, 0] < 345)]

                else:
                    peaks_90 = None

            else:
                peaks_90 = None

            # Check to make sure that there are qualified peaks
            if peaks_90 is not None and peaks_90.shape[0] > 0:
                # Assign the last peak of the year as the first potential spring timing
                PH1_start = peaks_90[-1,0]
                PH1_poten = np.arange(PH1_start - 2, PH1_start + 3).astype(np.int64)
                max_flow_check = np.argmax(flow_data[PH1_poten])
                
                springindex_PH1 = int(peaks_90[-1, 0]) - 4 + max_flow_check
                # Check to see if this peak is also the fall pulse
                if (springindex_PH1 <= 75) and (len(peaks_90) < 2):
                    springindex_PH1 = None

            else:
                springindex_PH1 = None

            # Find the index of flows at or above the 90th percentile
            highflows = np.where(flow_data >= quants[1])[0]

            # Assign the last index above 90th percentile flow as the second potential spring recession index
            springindex_PH2 = np.max(highflows)

            # If the first placeholder is not valid, then use the second placeholder value
            if springindex_PH1 is None:
                # Set the index of the spring timing to the second placeholder
                springindex = springindex_PH2
            else:
                # Otherwise, set the spring index to the first placement
                springindex = springindex_PH1 + 2

            # Set the spring timing to the index identified
            SP_Tim.append(springindex)
            SP_Mag.append(flow_data[springindex])

        # Make a new data frame with just the flows after the top of the spring recession
        flow_post_SP = flow_data[springindex:]

        # Set a min flow threshold for the dry season to start based on the spring and min dry season baseflow
        min_summer_flow_percent = 0.125
        WY_max_flow = np.max(flow_data)
        post_SP_min_flow = np.min(flow_post_SP)
        Min_DS_Threshold = post_SP_min_flow + (WY_max_flow - post_SP_min_flow) * min_summer_flow_percent

        # Calculate the dry season start timing by subtracting the length of the water year by the time remaining
        # after the spring recession peak and then add the timing of the start of the dry season after the spring peak
        PH_DS_Tim = Altered_Summer_Dry_Season_Tim_Varied(flow_post_SP, flow_thresh=Min_DS_Threshold)
        roc = np.diff(flow_post_SP) / flow_post_SP[:-1]
        roc = np.nan_to_num(roc, nan=0)
        roc = np.insert(roc, 0, np.nan)
        if PH_DS_Tim is None:
            DS_Tim.append(-9999)
            SP_ROC.append(-9999)
            SP_ROC_Max.append(-9999)
            SP_Dur.append(-9999)
            continue
            
        if PH_DS_Tim is not None and PH_DS_Tim == 0:
            PH_DS_Tim = 1
        
        
        DS_Tim.append(PH_DS_Tim + springindex)
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
        "SP_Tim": SP_Tim,
        "SP_Mag": SP_Mag,
        "SP_ROC": SP_ROC,
        "SP_Dur": SP_Dur,
        "SP_ROC_Max": SP_ROC_Max,
        "DS_Tim": DS_Tim
    }
    # Return all of the metrics
    return SP_Metrics_and_Dry_Season_Tim
