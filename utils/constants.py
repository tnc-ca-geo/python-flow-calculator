VERSION = '0.9.7'
WY_START_DATE = '10/1'
DELETE_INDIVIDUAL_FILES_WHEN_BATCH = True
QUIT_ON_ERROR = False # do you want the entire process to stop when an error occurs, True assumes you want more detailed messages as you are hopefully debugging it
SKIP_PROMPTS_BATCH = True # do you want to skip the prompts confirming you want to continue?
PRODUCE_DRH = False
TYPES = {
    'all_year_average_annual_flows': "Avg",
    'all_year_standard_deviations': "Std",
    'all_year_coefficient_variations': "CV",
    'spring_timings_julian': "SP_Tim_julian",
    'spring_timings_water': "SP_Tim",
    'spring_magnitudes': "SP_Mag",
    'spring_durations': "SP_Dur",
    'spring_rocs': "SP_ROC",
    'summer_timings_julian': "DS_Tim_julian",
    'summer_timings_water': "DS_Tim",
    'summer_magnitudes_ninety': "DS_Mag_90",
    'summer_magnitudes_fifty': "DS_Mag_50",
    'summer_durations_flush': "DS_Dur_WSI",
    'summer_durations_wet': "DS_Dur_WS",
    'summer_no_flow_counts': "DS_No_Flow",
    'fall_timings_julian': "FA_Tim_julian",
    'fall_timings_water': "FA_Tim",
    'fall_magnitudes': "FA_Mag",
    'fall_durations': "FA_Dur",
    'wet_wet_timings_julian': "Wet_Tim_julian",
    'wet_wet_timings_water': "Wet_Tim",
    'wet_baseflows_10': "Wet_BFL_Mag_10",
    'wet_baseflows_50': "Wet_BFL_Mag_50",
    'wet_bfl_durs': "Wet_BFL_Dur",

    'winter_timings__two': "Tim_2",
    'winter_timings__five': "Tim_5",
    'winter_timings__ten': "Tim_10",
    'winter_timings__twenty': "Tim_20",
    'winter_timings__fifty': "Tim_50",
    'winter_magnitudes__two': "High_2",
    'winter_magnitudes__five': "High_5",
    'winter_magnitudes__ten': "High_10",
    'winter_magnitudes__twenty': "High_20",
    'winter_magnitudes__fifty': "High_50",
    'winter_durations__two': "Dur_2",
    'winter_durations__five': "Dur_5",
    'winter_durations__ten': "Dur_10",
    'winter_durations__twenty': "Dur_20",
    'winter_durations__fifty': "Dur_50",
    'winter_frequencys__two': "Fre_2",
    'winter_frequencys__five': "Fre_5",
    'winter_frequencys__ten': "Fre_10",
    'winter_frequencys__twenty': "Fre_20",
    'winter_frequencys__fifty': "Fre_50",

    # Exceedance percentiles translated to recurrence intervals for output: exc_50 -> peak_2, exc_20 -> peak_5, exc_10 -> peak_10, exc_5 -> peak_20, exc_2 -> peak_50 
    'winter_timings_two': "Peak_Tim_50",
    'winter_timings_five': "Peak_Tim_20",
    'winter_timings_ten': "Peak_Tim_10",
    'winter_timings_twenty': "Peak_Tim_5",
    'winter_timings_fifty': "Peak_Tim_2",
    'winter_magnitudes_two': "Peak_50",
    'winter_magnitudes_five': "Peak_20",
    'winter_magnitudes_ten': "Peak_10",
    'winter_magnitudes_twenty': "Peak_5",
    'winter_magnitudes_fifty': "Peak_2",
    'winter_durations_two': "Peak_Dur_50",
    'winter_durations_five': "Peak_Dur_20",
    'winter_durations_ten': "Peak_Dur_10",
    'winter_durations_twenty': "Peak_Dur_5",
    'winter_durations_fifty': "Peak_Dur_2",
    'winter_frequencys_two': "Peak_Fre_50",
    'winter_frequencys_five': "Peak_Fre_20",
    'winter_frequencys_ten': "Peak_Fre_10",
    'winter_frequencys_twenty': "Peak_Fre_5",
    'winter_frequencys_fifty': "Peak_Fre_2",
    # : "Peak_Dur_2": "Peak_Fre_2": "Peak_Mag_2": "Peak_Tim_5": "Peak_Dur_5": "Peak_Fre_5": "Peak_Mag_5": "Peak_Tim_10": "Peak_Dur_10": "Peak_Fre_10": "Peak_Mag_10": "Peak_Tim_20": "Peak_Dur_20": "Peak_Fre_20": "Peak_Mag_20"

    'ds_low_min_avgs': "DS_7d_Low_Mag",
    'ds_low_min_date': "DS_7d_Low_Tim",
    'ds_first_zero': "DS_No_Flow_Tim",
    'ds_zeros_per_year': "DS_No_Flow_Dur",
    'Overall_Int_Class': "Overall_Int_Class",
    'Int_Class': "Int_Class",
    'wyt': "WYT"
}
NUMBER_TO_CLASS = {1: 'SM', 2: 'HSR', 3: 'LSR', 4: 'WS', 5: 'GW', 6: 'PGR', 7: 'FER', 8: 'RGW', 9: 'HLP', 10: 'NA'}
CLASS_TO_NUMBER = {value: key for key, value in NUMBER_TO_CLASS.items()}
REQUIRED_BATCH_COLUMNS = ['usgs', 'cdec', 'path', 'comid', 'class', 'lat', 'lng', 'calculator']
