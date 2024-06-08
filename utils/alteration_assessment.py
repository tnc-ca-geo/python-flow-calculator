import pandas as pd
import numpy as np
import requests
import os
from io import StringIO

def assess_alteration(gages, metrics_paths, output_files = 'user_output_files', aa_start_year = None, aa_end_year = None):
    
    return_message = ''
    alteration_assessment_list = []
    for (gage, metrics) in zip(gages, metrics_paths):
        comid = gage.comid
        gage_id = gage.gage_id
            
        predicted_metrics = get_predicted_flow_metrics(comid)
        if predicted_metrics.empty:
            return_message = return_message + f"Predicted metrics could not be generated for comid {comid}. Is it outside the study area? Skipping it...\n"
            continue
        
        formatted_percentiles, formatted_raw, count = format_metrics(metrics,aa_start_year=aa_start_year, aa_end_year= aa_end_year)

        if formatted_raw.empty:
            return_message = return_message + f"The time range you selected {aa_start_year}-{aa_end_year} leaves the gage {gage_id} with no data. Skipping it...\n"
            continue

        output_df = compare_data_frames(formatted_raw, predicted_metrics, formatted_percentiles,count)
        
        aa_dict = {}
        aa_dict['aa'] = output_df.copy(deep = True)
        aa_dict['gage_id'] = gage_id
        alteration_assessment_list.append(aa_dict)
    
    if len(alteration_assessment_list) > 0:
        write_alteration_assessment(alteration_assessment_list, output_files)
    return return_message

def assess_alteration_by_wyt(gages, metrics_paths, output_files = 'user_output_files', aa_start_year = None, aa_end_year = None):
    
    return_message = ''
    alteration_assessment_list = []
    for (gage, metrics) in zip(gages, metrics_paths):
        comid = gage.comid
        gage_id = gage.gage_id
            
        for wyt in ('dry', 'wet', 'moderate'):
            predicted_metrics = get_predicted_flow_metrics(comid, wyt=wyt)
            
            if predicted_metrics.empty:
                return_message = return_message + f"Predicted metrics could not be generated for comid {comid} and water year type {wyt}. Is this comid outside the study area? Skipping it...\n"
                continue
            
            formatted_percentiles, formatted_raw, count = format_metrics(metrics, wyt = wyt, aa_start_year = aa_start_year, aa_end_year = aa_end_year)
            
            if formatted_raw.empty:
                return_message = return_message + f"The year range selected {aa_start_year}-{aa_end_year} leaves the gage {gage_id} with no data for water year type {wyt}. Skipping it...\n"
                continue

            output_df = compare_data_frames(formatted_raw, predicted_metrics, formatted_percentiles, count)
            
            output_df.insert(0, 'WYT', wyt)
            aa_dict = {}
            aa_dict['aa'] = output_df.copy(deep = True)
            aa_dict['gage_id'] = gage_id
            alteration_assessment_list.append(aa_dict)
    
    if len(alteration_assessment_list) > 0:
        write_alteration_assessment(alteration_assessment_list, output_files, wyt = True)        
    
    return return_message

def compare_data_frames(raw_metrics, predicted_metrics, raw_percentiles, count):
    
    combined_df = pd.merge(raw_percentiles, predicted_metrics, on='metric', suffixes=('', '_predicted'))
    combined_df['alteration_type'] = "unknown"
    combined_df['status'] = "indeterminate"
    combined_df['status_code'] = 0
    combined_df['median_in_iqr'] = False

    # This is for Ted if he still uses this tool
    combined_df['median_in_iqr'] = np.where(((combined_df['p50'] <= combined_df['p75_predicted']) & (combined_df['p50'] >= combined_df['p25_predicted'])), True, combined_df['median_in_iqr'])
    
    combined_df['alteration_type'] = np.where(combined_df['p50'] < combined_df['p25_predicted'], 'low', combined_df['alteration_type'])
    combined_df['alteration_type'] = np.where(combined_df['p50'] > combined_df['p75_predicted'], 'high', combined_df['alteration_type'])
    
    for index, row in combined_df.iterrows():
        if (row['p50'] >= row['p10_predicted']) and (row['p50'] <= row['p90_predicted']):
            if not observations_altered(observations=raw_metrics, metric = row['metric'], low_bound=row['p10_predicted'], high_bound=row['p90_predicted'], median = row['p50']):
                combined_df.at[index, 'status_code'] = 1
                combined_df.at[index, 'status'] = "likely_unaltered"
                combined_df.at[index, 'alteration_type'] = "none_found"
        else:
            combined_df.at[index, 'status'] = "likely_altered"
            combined_df.at[index, 'status_code'] = -1

    count = count.to_frame()
    count.columns = ['years_used']
    count['metric'] = count.index
    combined_df = pd.merge(combined_df, count, on='metric')
    combined_df['sufficient_data'] = np.where(combined_df['years_used'] < 10, False, True)

    return combined_df

def write_alteration_assessment(aa_list, output_dir, wyt = False):
    
    first_df = True
    out_df = None
    
    for dict in aa_list:
        df = dict['aa']
        gage_id = dict['gage_id']
        peaks = ('Peak_10', 'Peak_5', 'Peak_2')
        df = df[~df['metric'].isin(peaks)]
        timing_cols = ['DS_Tim', 'FA_Tim', 'SP_Tim', 'Wet_Tim']
        condition = (df['metric'].isin(timing_cols)) & (df['alteration_type'] == 'low')
        df.loc[condition, 'alteration_type'] = 'early'
        condition = (df['metric'].isin(timing_cols)) & (df['alteration_type'] == 'high')
        df.loc[condition, 'alteration_type'] = 'late'

        df.insert(0, 'Source', gage_id)
        if first_df:
            out_df = df
            first_df = False
        else:
            out_df, df
            out_df = pd.concat([out_df,df], ignore_index=True)
    
    file_string = 'combined'
    list_to_add = []
    if (len(aa_list) == 1) or (wyt and len(aa_list) <= 3):
        file_string = gage_id
        list_to_add = ['Source']

    if wyt:
        out_path = os.path.join(output_dir,f'{file_string}_wyt_alteration_assessment.csv')
        alteration_results = out_df[list_to_add + ['WYT' ,'metric','alteration_type', 'status', 'status_code', 'median_in_iqr', 'years_used', 'sufficient_data']]
    else:
        out_path = os.path.join(output_dir,f'{file_string}_alteration_assessment.csv')
        alteration_results = out_df[list_to_add + ['metric','alteration_type', 'status', 'status_code', 'median_in_iqr', 'years_used', 'sufficient_data']]
    
    alteration_results.to_csv(out_path, index = False)
    
    if wyt:
        out_path = os.path.join(output_dir,f'{file_string}_wyt_predicted_observed_percentiles.csv')
        percentiles = out_df[['Source', 'WYT', 'metric', 'p10', 'p25', 'p50', 'p75', 'p90', 'p10_predicted', 'p25_predicted', 'p50_predicted', 'p75_predicted', 'p90_predicted']]
    else:
        out_path = os.path.join(output_dir,f'{file_string}_predicted_observed_percentiles.csv')
        percentiles = out_df[['Source', 'metric', 'p10', 'p25', 'p50', 'p75', 'p90', 'p10_predicted', 'p25_predicted', 'p50_predicted', 'p75_predicted', 'p90_predicted']]

    percentiles = out_df[['Source', 'metric', 'p10', 'p25', 'p50', 'p75', 'p90', 'p10_predicted', 'p25_predicted', 'p50_predicted', 'p75_predicted', 'p90_predicted']]
    percentiles.to_csv(out_path, index = False)

def observations_altered(observations, metric, low_bound, high_bound, median):
    obs = pd.to_numeric(observations[metric], errors = 'coerce')
    obs = obs.fillna(median)
    
    percentage = ((obs > high_bound) & (obs < low_bound)).mean() * 100
    if percentage > 50:
        return True
    else:
        return False


def format_metrics(file_path, wyt = None, aa_start_year = None, aa_end_year = None):
    
    metric_data = pd.read_csv(file_path, header=None).T
    metric_data.columns = metric_data.iloc[0]    
    metric_data.drop(0,inplace=True)
    metric_data = metric_data.astype({'Year':'int'})
    if aa_start_year is not None:
        metric_data.drop(metric_data[metric_data.Year < aa_start_year].index, inplace=True)
    if aa_end_year is not None:
        metric_data.drop(metric_data[metric_data.Year > aa_end_year].index, inplace=True)
    if wyt is not None:
        metric_data = metric_data.loc[metric_data['WYT'] == wyt]
    if metric_data.empty:
        return None, metric_data, None
    count = metric_data.count(axis = 0)
    metric_data = metric_data.drop(columns=['WYT'])
    metric_columns = metric_data.columns.difference(['Year'])
    melted_df = pd.melt(metric_data, id_vars=['Year'], value_vars=metric_columns, var_name='metric', value_name='value')
    melted_df['value'] = pd.to_numeric(melted_df['value'], errors='coerce')
    percentiles_df = melted_df.groupby(['metric'])['value'].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).unstack().reset_index()
    percentiles_df.columns = ['metric', 'p10', 'p25', 'p50', 'p75', 'p90']
    return percentiles_df, metric_data, count


def get_predicted_flow_metrics(comid, wyt="all"):
    url = f"https://flow-api.codefornature.org/v2/ffm/?comids={comid}"
    response = requests.get(url)
    if response.status_code == 200:
        content = StringIO(response.text)
        metrics_full = pd.read_csv(content)
        if wyt != "any":
            metrics_filtered = metrics_full[metrics_full['wyt'] == wyt]
            metrics_filtered = metrics_filtered.drop(columns=['wyt'])
            deduplicated = metrics_filtered[metrics_filtered['source'].isin(['model', 'inferred'])]
        else:
            metrics_filtered = metrics_full.copy()
            deduplicated = metrics_filtered[metrics_filtered['source'].isin(['model', 'inferred'])]

        deduplicated = deduplicated.drop(columns=['gage_id', 'observed_years','alteration','source','comid'])
        deduplicated = fill_na_10th_percentile(deduplicated)
        return replace_ffm_column(deduplicated)
        
    else:
        raise Exception(f"Failed to fetch predicted metrics from flow-api does this comid exist {comid}?")


    

def replace_ffm_column(df):  
    mapping_dict = {
    "ds_mag_50": "DS_Mag_50",
    "ds_mag_90": "DS_Mag_90",
    "ds_dur_ws": "DS_Dur_WS",
    "ds_tim": "DS_Tim",
    "fa_tim": "FA_Tim",
    "fa_dur": "FA_Dur",
    "fa_mag": "FA_Mag",
    "peak_10": "Peak_10",
    "peak_2": "Peak_2",
    "peak_5": "Peak_5",
    "peak_dur_10": "Peak_Dur_10",
    "peak_dur_2": "Peak_Dur_2",
    "peak_dur_5": "Peak_Dur_5",
    "peak_fre_10": "Peak_Fre_10",
    "peak_fre_2": "Peak_Fre_2",
    "peak_fre_5": "Peak_Fre_5",
    "sp_dur": "SP_Dur",
    "sp_mag": "SP_Mag",
    "sp_tim": "SP_Tim",
    "sp_roc": "SP_ROC",
    "wet_bfl_dur": "Wet_BFL_Dur",
    "wet_bfl_mag_10": "Wet_BFL_Mag_10",
    "wet_bfl_mag_50": "Wet_BFL_Mag_50",
    "wet_tim": "Wet_Tim"
    }
    
    df["ffm"] = df["ffm"].map(mapping_dict)
    df = df.rename(columns={"ffm": "metric"})
    df = df.drop(columns=["unit", "observed_year_start", "observed_year_end"])
    
    return df


def fill_na_10th_percentile(df):
    if df['p10'].isna().any():

        condition = (df['p10'].isna()) & (df['p25'] == 0)
        df.loc[condition, 'p10'] = 0
        warning_msg = "Predicted flow metrics have NA values in the 10th percentile column - they have been filled with 0 values where the 25th percentile value is 0 and left as is otherwise"
        print(warning_msg)
        
        if df['p10'].isna().any():
            warning_msg = "Unfilled NAs remain in the p10 column - we can't safely fill these because the p25 column is greater than 0 - this will likely break the code later in the package, so expect an error! These NA values should be addressed more broadly by the CEFF tech team."
            print(warning_msg)
    
    return df