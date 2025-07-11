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
    output_file_dirs = [[],[]]
    metadata_files = []
    file_identifiers = []
    file_base_name = ['annual_flow_matrix', 'annual_flow_result']


    for gage in gage_arr:

        try:

            file = gage.download_directory
            file_name = os.path.join(output_files, os.path.splitext(os.path.basename(file))[0])
            dataset, csv_warning_message = read_csv_to_arrays(file)
            warning_message += csv_warning_message
            matrix = MatrixConversion(
                dataset['date'], dataset['flow'], start_date)
            results, used_calculator, results_message = get_results(matrix, int(gage.flow_class), start_date, gage.comid, gage.selected_calculator)
            warning_message += results_message
            output_dir0 = write_annual_flow_matrix(file_name, results, file_base_name[0])
            output_dir1 = write_annual_flow_result(file_name, results, file_base_name[1])
            if PRODUCE_DRH:
                write_drh(file_name, results, 'drh')
            formatted = f'{gage.gage_id}'
            param_path = os.path.join(output_files,formatted)
            metadata_file = write_parameters(param_path, gage, used_calculator, aa_start_year, aa_end_year)

            file_identifiers.append(os.path.splitext(os.path.basename(file))[0])
            output_file_dirs[0].append(output_dir0)
            output_file_dirs[1].append(output_dir1)
            metadata_files.append(metadata_file)
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
            if not file_paths:
                warning_message += f"There is no {base_name} files to batch together, all gages likely errored proceeding to the next file type...\n"
            else:
                batch_files(file_paths, base_name, file_identifiers, output_files, alteration_needed)
        # the format of these files is very different so they need to be batched separately, they could be done in the same function with a bunch of conditionals but I think thats less clean
        batch_metadata_files(metadata_files, file_identifiers, output_files)


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
    results["all_year"], return_message = calculator.all_year()
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
    return results, return_message

def calc_results_reference(matrix, flow_class, start_date = '10/1', comid = None):
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
    results["all_year"], return_message = calculator.all_year()
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
    return results, calculator.calc_RBFI(), calc_avg_nan_per_year(copy.deepcopy(results)), return_message

def get_results(matrix, flow_class, start_date = None, comid = None, desired_calculator = None):
    if flow_class is None or flow_class == 10:
        flow_class = 3
    if desired_calculator is None:
        # no specified calculator, determine which is better

        if int(flow_class) == 7:
            flashy_res, calc_return_message = calc_results_flashy(matrix, flow_class, start_date, comid)
            return flashy_res, 'Flashy (Class 7)', calc_return_message
        else:
            reference_res, rbfi, annual_nan, calc_return_message = calc_results_reference(copy.deepcopy(matrix), flow_class, start_date, comid)

            if(rbfi + annual_nan > 0.8):
                flashy_res, calc_return_message = calc_results_flashy(matrix, flow_class, start_date, comid)
                return flashy_res, 'Flashy (RBFI + mean annual nan > 0.8)', calc_return_message
            else:
                return reference_res, 'Reference (RBFI + mean annual nan <= 0.8)', calc_return_message

    elif desired_calculator.lower() == 'reference':
        # use the reference calculator
        reference_res, _, _, calc_return_message = calc_results_reference(matrix, flow_class, start_date, comid)
        return reference_res, 'Reference (User Specified)', calc_return_message
    elif desired_calculator.lower() == 'flashy':
        # use the ucdavis flashy calculator
        flashy_res,calc_return_message = calc_results_flashy(matrix, flow_class, start_date, comid)
        return flashy_res, 'Flashy (User Specified)', calc_return_message

def write_annual_flow_matrix(file_name, results, file_type):
    flow_matrix = np.array(results['flow_matrix']).T
    year_column = np.array(results['year_ranges'])
    flow_matrix = np.c_[year_column, flow_matrix]
    days_header = 'Year,' + ','.join(str(day) for day in range(1, 367))
    output_dir = file_name + '_' + file_type + '.csv'
    np.savetxt(output_dir, flow_matrix, delimiter=',',
               header=days_header, fmt='%s', comments='')

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
    # remove summer no_flow from main output but save it for supplementary outputs

    dataset = []
    # dict_to_array(result['all_year'], 'all_year', dataset)
    dict_to_array(results['fall'], 'fall', dataset)
    dict_to_array(results['wet'], 'wet', dataset)
    dict_to_array(results['winter'], 'winter', dataset)
    dict_to_array(results['spring'], 'spring', dataset)
    dict_to_array(results['summer'], 'summer', dataset)
    dict_to_array(results['new_low'], 'ds', dataset)
    dict_to_array(results['classification'], '', dataset)
    dataset.append(['Avg'] + results['all_year']
                            ['average_annual_flows'])
    dataset.append(['Std'] + results['all_year']
                            ['standard_deviations'])
    dataset.append(['CV'] + results['all_year']
                            ['coefficient_variations'])
    results['year_ranges'].insert(0,'Year')
    df = pd.DataFrame(dataset)
    df.columns = results['year_ranges']
    df = df.set_index(df.columns[0])
    df = df.T
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Year'}, inplace=True)
    df = df[~df[['DS_Tim', 'SP_Tim', 'Wet_Tim', 'FA_Tim']].isnull().all(axis=1)]
    output_dir = file_name + '_' + file_type + '.csv'
    df.to_csv(output_dir, index=False)
    return output_dir

def write_parameters(file_name, gage_object, used_calculator, aa_start = None, aa_end = None, file_type = 'run_metadata'):
    # List of all the calculator used strings that want the flashy params outputted
    used_flashy  = ["Flashy (Class 7)","Flashy (User Specified)","Flashy (RBFI + mean annual nan > 0.8)"]
    # list of all the calculator used strings that want the reference calculator params outputted
    used_reference = ["Flashy (RBFI + mean annual nan > 0.8)", "Reference (RBFI + mean annual nan <= 0.8)", "Reference (User Specified)"]
    now = datetime.now()
    timestamp = now.strftime("%m/%d/%Y, %H:%M")
    if aa_start and aa_end:
        cols = {'Date_time': timestamp, 'Input_File_Name': gage_object.download_directory, 'Stream_class': NUMBER_TO_CLASS[gage_object.flow_class], 'Used_Calculator': used_calculator, 'Used_COMID': gage_object.comid, 'Alteration Assessment range': f'{aa_start}-{aa_end}'}
    else:
        cols = {'Date_time': timestamp,'Input_File_Name': gage_object.download_directory, 'Stream_class': NUMBER_TO_CLASS[gage_object.flow_class], 'Used_Calculator': used_calculator, 'Used_COMID': gage_object.comid}
    df = pd.DataFrame(cols, index=[0])
    if used_calculator in used_reference:
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

def batch_metadata_files(metadata_file_paths, file_identifier, output_dir):
    column_names = ['Parameter Name/Section Name', 'Parameter Value']
    combined_data = pd.DataFrame()
    for file_path, file_id in zip(metadata_file_paths, file_identifier):
        current_data = pd.read_csv(file_path, header=None, names = column_names)
        current_data['Source'] = file_id
        if combined_data.empty:
            combined_data = current_data
        else:
            combined_data = pd.concat([combined_data,current_data])
        if os.path.isfile(file_path) and DELETE_INDIVIDUAL_FILES_WHEN_BATCH:
            os.remove(file_path)
    column_order = ['Source'] + column_names
    combined_data = combined_data[column_order]
    combined_data.to_csv(os.path.join(output_dir, "combined_metadata.csv"), index=False)

def batch_files(file_paths, base_file_name, file_identifier, output_dir, alteration_needed):

    combined_data = pd.DataFrame()

    for file_path, file_id in zip(file_paths, file_identifier):

        current_data = pd.read_csv(file_path, header=0, dtype=str)
        current_data['Source'] = file_id
        if combined_data.empty:
            combined_data = current_data
        else:
            combined_data = pd.concat([combined_data,current_data])
        if os.path.isfile(file_path) and DELETE_INDIVIDUAL_FILES_WHEN_BATCH:
            if not (alteration_needed and base_file_name == 'annual_flow_result'):
                os.remove(file_path)

    column_order = ['Source'] + [col for col in combined_data.columns if col != 'Source']
    combined_data = combined_data[column_order]
    combined_data.to_csv(os.path.join(output_dir, "combined_" + base_file_name + ".csv"), index=False)

def read_csv_to_arrays(file_path):
    warning_message = ''

    df = pd.read_csv(file_path, skipinitialspace=True)
    df.columns = df.columns.str.lower()

    date_column = 'date'
    flow_column = 'flow' if 'flow' in df.columns else 'discharge' if 'discharge' in df.columns else None

    if flow_column is None:
        raise ValueError("Neither 'flow' nor 'discharge' column found in the CSV.")

    df = df[[date_column, flow_column]]
    try:
        df[flow_column] = pd.to_numeric(df[flow_column],errors='raise')
    except Exception as e:
        warning_message += f'The provided "{flow_column}" column within {file_path} is not strictly numeric (contains some non numeric characters in some entries), these rows will be ignored and treated as missing. Please review your csv file if this is unexpected.\n'
        df[flow_column] = pd.to_numeric(df[flow_column], errors='coerce')

    # Count negative values in the flow_column
    num_negative_values = (df[flow_column] < 0).sum()

    if num_negative_values > 0:
        warning_message += f"Found {num_negative_values} negative values in the provided '{flow_column}' column within {file_path}. Some gages use large negative values to represent missing values and others naturally observe them when influenced by the tide. If this count seems higher then expected please review the data. These rows will be ignored and treated as missing.\n"

    # Replace negative values with NaN
    df.loc[df[flow_column] < 0, flow_column] = np.nan

    try:
        dates = pd.to_datetime(df[date_column], errors='raise')
    except Exception as e:
        warning_message += f'The provided "{date_column}" column within {file_path} has entries that are unparsable as dates, please ensure the "{date_column}" column has one consistent date format and all entries are dates. This data will likely crash the calculator in one of the next steps.\n'
        dates = pd.to_datetime(df[date_column], errors='coerce')

    flow = df[flow_column]

    return {'date': dates, 'flow': flow}, warning_message