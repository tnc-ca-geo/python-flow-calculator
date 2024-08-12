from datetime import datetime
import os
import copy
import numpy as np
import pandas as pd
from classes.FlashyMetricCalculator import FlashyCalculator
from classes.matrix_convert import MatrixConversion
from classes.MetricCalculator import Calculator
from utils.helpers import calc_avg_nan_per_year, comid_to_wyt, dict_to_array
from utils.constants import DELETE_INDIVIDUAL_FILES_WHEN_BATCH, QUIT_ON_ERROR, NUMBER_TO_CLASS, PRODUCE_DRH
from params import summer_params
from params import fall_params
from params import spring_params
from params import winter_params
from params import flashy_params


def upload_files(start_date, gage_arr, output_files = 'user_output_files', batched = False, alteration_needed = False, aa_start_year = None, aa_end_year = None):
    
    warning_message = ''

    # these 3 are for storing file names and file types of files that will later need to be batched together 
    output_file_dirs = [[],[],[]]
    file_identifiers = []
    file_base_name = ['annual_flow_matrix', 'annual_flow_result', 'supplementary_metrics']
    
    
    for gage in gage_arr:
        
        try:
            
            file = gage.download_directory
            file_name = os.path.join(output_files, os.path.splitext(os.path.basename(file))[0])
            dataset = read_csv_to_arrays(file)
            matrix = MatrixConversion(
                dataset['date'], dataset['flow'], start_date)
            results, used_calculator = get_results(matrix, int(gage.flow_class), start_date, gage.comid, gage.selected_calculator)
            output_dir0 = write_annual_flow_matrix(file_name, results, file_base_name[0])
            output_dir1, output_dir2 = write_annual_flow_result(file_name, results, file_base_name[1])
            if PRODUCE_DRH:
                write_drh(file_name, results, 'drh')
            formatted = f'{gage.gage_id}'
            param_path = os.path.join(output_files,formatted)
            write_parameters(param_path, gage.flow_class, used_calculator, aa_start_year, aa_end_year)

            file_identifiers.append(os.path.splitext(os.path.basename(file))[0])
            output_file_dirs[0].append(output_dir0)
            output_file_dirs[1].append(output_dir1)
            output_file_dirs[2].append(output_dir2)
        except Exception as e:
            original_message = str(e)
            gage_message = f"ERROR PROCESSING GAGE: {gage}"
            if QUIT_ON_ERROR:
                raise type(e)(f"{original_message}. \n{gage_message}")
            else:
                warning_message += f"There was an error when calculating metrics for gage {gage} proceeding to next gage\n"
                continue
    
    
    if batched:
        for file_paths, base_name in zip(output_file_dirs, file_base_name):
            print(f'FILE PATH: {file_paths}, FILE BASE_NAME: {file_base_name}')
            if not file_paths:
                warning_message += f"There is no {base_name} files to batch together, all gages likely errored proceeding to the next file type...\n"
            else:
                batch_files(file_paths, base_name, file_identifiers, output_files, alteration_needed)



    return output_file_dirs[1], warning_message

def calc_results_flashy(matrix, flow_class, start_date = '10/1', comid = None):
    results = {}
    results["year_ranges"] = [int(i) + 1 for i in matrix.year_array]
    results["flow_matrix"] = np.where(
        pd.isnull(matrix.flow_matrix), None, matrix.flow_matrix).tolist()
    results["start_date"] = matrix.start_date
    calculator = FlashyCalculator(
    matrix.flow_matrix, matrix.years_array, flow_class, results["year_ranges"][0], start_date)
    results["wet"] = {}
    results["spring"] = {}
    results["summer"] = {}
    results["all_year"] = calculator.all_year()
    results["winter"] = calculator.winter_highflow_annual()
    results["spring"], start_of_summer = calculator.dry_spring_timings()
    results["fall"], fall_wet_timings = calculator.fall_flush_timings_durations()
    results["wet"] = calculator.fall_winter_baseflow()
    results["wet"]["wet_timings_water"] = fall_wet_timings
    results["summer"] = calculator.summer_baseflow_durations_magnitude()
    results["summer"]["timings_water"] = start_of_summer
    results["DRH"] = calculator.get_DRH()
    results["new_low"], results["classification"] = calculator.new_low_flow_metrics()
    if comid is not None:
        results["classification"]["wyt"] = [comid_to_wyt(comid,i) for i in results["year_ranges"]]
    return results

def calc_results_original(matrix, flow_class, start_date = '10/1', comid = None):
    results = {}
    results["year_ranges"] = [int(i) + 1 for i in matrix.year_array]
    results["flow_matrix"] = np.where(
        pd.isnull(matrix.flow_matrix), None, matrix.flow_matrix).tolist()
    results["start_date"] = matrix.start_date

    calculator = Calculator(
        matrix.flow_matrix, matrix.years_array, flow_class, results["year_ranges"][0], start_date)
    results["wet"] = {}
    results["spring"] = {}
    results["summer"] = {}
    results["all_year"] = calculator.all_year()
    results["winter"] = calculator.winter_highflow_annual()
    start_of_summer = calculator.start_of_summer()
    results["fall"], fall_wet_timings = calculator.fall_flush_timings_durations()
    results["spring"] = calculator.spring_transition_timing_magnitude()
    results["spring"]["durations"] = calculator.spring_transition_duration()
    results["spring"]["rocs"] = calculator.spring_transition_roc()
    results["wet"] = calculator.fall_winter_baseflow()
    results["wet"]["wet_timings_water"] = fall_wet_timings
    results["summer"] = calculator.summer_baseflow_durations_magnitude()
    results["summer"]["timings_water"] = start_of_summer
    results["DRH"] = calculator.get_DRH()
    results["new_low"], results["classification"] = calculator.new_low_flow_metrics()
    if comid is not None:
        results["classification"]["wyt"] = [comid_to_wyt(comid,i) for i in results["year_ranges"]]
    return results, calculator.calc_RBFI(), calc_avg_nan_per_year(copy.deepcopy(results)) 

def get_results(matrix, flow_class, start_date = None, comid = None, desired_calculator = None):
    if flow_class is None or flow_class == 10:
        flow_class = 3

    if desired_calculator is None:
        # no specified calculator, determine which is better
    
        if int(flow_class) == 7:
            flashy_res = calc_results_flashy(matrix, flow_class, start_date, comid)
            return flashy_res, 'Flashy (Class 7)'
        else:
            original_res, rbfi, annual_nan = calc_results_original(copy.deepcopy(matrix), flow_class, start_date, comid)
            
            if(rbfi + annual_nan > 0.8):
                flashy_res = calc_results_flashy(matrix, flow_class, start_date, comid)
                return flashy_res, 'Flashy (RBFI + mean annual nan > 0.8)'
            else:
                return original_res, 'Original (RBFI + mean annual nan <= 0.8)'
    
    elif desired_calculator.lower() == 'original':
        # use the original calculator
        original_res, _, _ = calc_results_original(matrix, flow_class, start_date, comid)
        return original_res, 'Original (User Specified)'
    elif desired_calculator.lower() == 'flashy':
        # use the ucdavis flashy calculator
        flashy_res = calc_results_flashy(matrix, flow_class, start_date, comid)
        return flashy_res, 'Flashy (User Specified)'
    
def write_annual_flow_matrix(file_name, results, file_type):
    year_ranges = 'Year,' +",".join(str(year) for year in results['year_ranges'])
    a = np.array(results['flow_matrix'])
    julian_date = np.arange(1, 367)
    a = np.c_[julian_date,a]
    output_dir = file_name + '_' + file_type + '.csv'
    np.savetxt(output_dir, a, delimiter=',',
                header=year_ranges, fmt='%s', comments='')
    return output_dir
        
def write_drh(file_name, results, file_type):  
    dataset = []
    for key, value in results['DRH'].items():
        data = value
        data.insert(0, key)
        dataset.append(data)

    a = np.array(dataset)
    output_dir = file_name + '_' + file_type + '.csv'
    np.savetxt(output_dir, a, delimiter=',', fmt='%s', comments='')
    return output_dir

def write_annual_flow_result(file_name, results, file_type):
    year_ranges = ",".join(str(year) for year in results['year_ranges'])
    # remove summer no_flow from main output but save it for supplementary outputs
    summer_no_flow = results['summer']['no_flow_counts']
    del results['summer']['no_flow_counts']

    dataset = []
    # dict_to_array(result['all_year'], 'all_year', dataset)
    dict_to_array(results['fall'], 'fall', dataset)
    dict_to_array(results['wet'], 'wet', dataset)
    dict_to_array(results['winter'], 'winter', dataset)
    dict_to_array(results['spring'], 'spring', dataset)
    dict_to_array(results['summer'], 'summer', dataset)
    dict_to_array(results['new_low'], 'ds', dataset)
    dict_to_array(results['classification'], '', dataset)
    results['year_ranges'].insert(0,'Year')
    df = pd.DataFrame(dataset)
    df.columns = results['year_ranges']
    output_dir = file_name + '_' + file_type + '.csv'
    df.to_csv(output_dir, index=False,na_rep='None')
    output_dir = file_name + '_' + file_type + '.csv'
    

    """Create supplementary metrics file"""
    supplementary = []
    supplementary.append(['Avg'] + results['all_year']
                            ['average_annual_flows'])
    supplementary.append(['Std'] + results['all_year']
                            ['standard_deviations'])
    supplementary.append(['CV'] + results['all_year']
                            ['coefficient_variations'])
    supplementary.append(['DS_No_Flow'] + summer_no_flow)
    output_dir2 = file_name + '_supplementary_metrics.csv'
    np.savetxt(output_dir2, supplementary, delimiter=',',
                fmt='%s', header='Year, ' + year_ranges, comments='')
    return output_dir, output_dir2

def write_parameters(file_name, flow_class, used_calculator, aa_start = None, aa_end = None, file_type = 'run_metadata'):
    # List of all the calculator used strings that want the flashy params outputted
    used_flashy  = ["Flashy (Class 7)","Flashy (User Specified)","Flashy (RBFI + mean annual nan > 0.8)"]
    # list of all the calculator used strings that want the original calculator params outputted
    used_original = ["Flashy (RBFI + mean annual nan > 0.8)", "Original (RBFI + mean annual nan <= 0.8)", "Original (User Specified)"]
    now = datetime.now()
    timestamp = now.strftime("%m/%d/%Y, %H:%M")
    if aa_start and aa_end:
        cols = {'Date_time': timestamp, 'Stream_class': NUMBER_TO_CLASS[flow_class], 'Used_Calculator': used_calculator, 'Alteration Assessment range': f'{aa_start}-{aa_end}'}
    else:
        cols = {'Date_time': timestamp, 'Stream_class': NUMBER_TO_CLASS[flow_class], 'Used_Calculator': used_calculator}
    df = pd.DataFrame(cols, index=[0])
    if used_calculator in used_original:
        df['Fall_params'] = '_'
        for key, value in fall_params.items():
            # modify all key names to make sure they are distinct from other dataframe entries (otherwise will not be added)
            key = key + '_fall'
            df[key] = value
        df['Wet_params'] = '_'
        for key, value in winter_params.items():
            key = key + '_wet'
            df[key] = value
        df['Spring_params'] = '_'
        for key, value in spring_params.items():
            key = key + '_spring'
            df[key] = value
        df['Dry_params'] = '_'
        for key, value in summer_params.items():
            key = key + '_dry'
            df[key] = value
    if used_calculator in used_flashy:
        df['Flashy_Calc_params'] = '_'
        for key, value in flashy_params.items():
            key = key + '_flashy_calc'
            df[key] = value
    df = df.transpose()
    output_dir = file_name + '_' + file_type +'.csv'
    df.to_csv(output_dir, sep=',', header=False)
    return output_dir

def batch_files(file_paths, base_file_name, file_identifier, output_dir, alteration_needed):
    
    combined_data = pd.DataFrame()

    for file_path, file_id in zip(file_paths, file_identifier):

        current_data = pd.read_csv(file_path, header=None).T
        current_data.columns = current_data.iloc[0]
        
        current_data.drop(0,inplace=True)
        current_data['Source'] = file_id
        if combined_data.empty:
            combined_data = current_data
        else:
            combined_data = pd.concat([combined_data,current_data])
        if os.path.isfile(file_path) and DELETE_INDIVIDUAL_FILES_WHEN_BATCH:
            if not (alteration_needed and base_file_name == 'annual_flow_result'):
                os.remove(file_path)
    
    column_order = ['Source'] + [col for col in combined_data.columns if col != 'Source']
    combined_data = combined_data.astype({'Year':'int'})
    combined_data = combined_data[column_order]
    combined_data.to_csv(os.path.join(output_dir, "combined_" + base_file_name + ".csv"), index=False)

def read_csv_to_arrays(file_path):
    fields = ['date', 'flow']

    df = pd.read_csv(file_path, skipinitialspace=True, usecols=fields)
    
    # Some gages use very large negative numbers to represent their missing values, turning them into nan which is how the calculator expects missing values
    df.loc[df['flow'] < 0, 'flow'] = np.nan
    
    dates = df['date']
    flow = df['flow']

    return {'date': dates, 'flow': flow}