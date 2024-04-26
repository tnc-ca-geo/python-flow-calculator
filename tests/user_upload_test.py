import os
import filecmp
import pytest
import glob
from utils.upload_files import upload_files  

EXPECTED_INPUT_OUTPUT_DIR = "test_files"
ACTUAL_OUTPUT_DIR = "output"

@pytest.mark.parametrize("input_filenames, output_filenames, start_date, flow_class", [
    (["tnc_input.csv"], ["tnc_input_supplementary_metrics.csv", "tnc_input_run_metadata.csv", "tnc_input_new_low_flow_metrics.csv","tnc_input_drh.csv","tnc_input_annual_flow_result.csv","tnc_input_annual_flow_matrix.csv"], "10/1",6),
    (["tnc_input_fc7.csv"], ["tnc_input_fc7_supplementary_metrics.csv", "tnc_input_fc7_run_metadata.csv", "tnc_input_fc7_new_low_flow_metrics.csv","tnc_input_fc7_drh.csv","tnc_input_fc7_annual_flow_result.csv","tnc_input_fc7_annual_flow_matrix.csv"], "10/1",7),
    (["zero_input.csv"], ["zero_input_supplementary_metrics.csv", "zero_input_run_metadata.csv", "zero_input_new_low_flow_metrics.csv","zero_input_drh.csv","zero_input_annual_flow_result.csv","zero_input_annual_flow_matrix.csv"], "10/1",6),
    (["tnc_input_date.csv"], ["tnc_input_date_supplementary_metrics.csv", "tnc_input_date_run_metadata.csv", "tnc_input_date_new_low_flow_metrics.csv","tnc_input_date_drh.csv","tnc_input_date_annual_flow_result.csv","tnc_input_date_annual_flow_matrix.csv"], "10/5",6),
    (["tnc_input.csv","zero_input.csv"], ["tnc_input_supplementary_metrics.csv", "tnc_input_run_metadata.csv", "tnc_input_new_low_flow_metrics.csv","tnc_input_drh.csv","tnc_input_annual_flow_result.csv","tnc_input_annual_flow_matrix.csv","zero_input_supplementary_metrics.csv", "zero_input_run_metadata.csv", "zero_input_new_low_flow_metrics.csv","zero_input_drh.csv","zero_input_annual_flow_result.csv","zero_input_annual_flow_matrix.csv"], "10/1",6),
    # new test cases go here
])
def test_file_upload(input_filenames, output_filenames, start_date, flow_class):
    expected_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),EXPECTED_INPUT_OUTPUT_DIR)
    actual_path = os.path.join(expected_path,ACTUAL_OUTPUT_DIR)
    input_paths = [os.path.join(expected_path, filename) for filename in input_filenames]
    actual_output_paths = [os.path.join(actual_path, filename) for filename in output_filenames]
    expected_output_paths = [os.path.join(expected_path, filename) for filename in output_filenames]
    
    upload_files(start_date,input_paths,flow_class,actual_path)

    # Check if output files are generated
    for output_path in actual_output_paths:
        assert os.path.exists(output_path), f"Expected output file {output_path} not found."

    # Check if contents of output files match expected contents
    for expected_file_path in expected_output_paths:
        directory, filename = os.path.split(expected_file_path)
        actual_file_path = os.path.join(directory, ACTUAL_OUTPUT_DIR, filename)
        if filename.endswith('run_metadata.csv'):
            with open(expected_file_path, 'r') as expected_file, open(actual_file_path, 'r') as actual_file:
                expected_lines = expected_file.readlines()
                actual_lines = actual_file.readlines()
                expected_lines[0] = ''
                actual_lines[0] = ''
                assert expected_lines == actual_lines, f"Contents of {actual_file_path} do not match expected contents in {expected_file_path}."
        else:
            assert filecmp.cmp(expected_file_path, actual_file_path), f"Contents of {actual_file_path} do not match expected contents in {expected_file_path}."
    # clean output dir so we dont get false positives
    for f in glob.glob(os.path.join(actual_path, '*')):
        if os.path.basename(f) != '.gitignore':
            os.remove(f)