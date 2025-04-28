from utils.upload_files import upload_files
from utils.constants import WY_START_DATE, DELETE_INDIVIDUAL_FILES_WHEN_BATCH, CLASS_TO_NUMBER, INPUT_FILE_DIR, OUTPUT_FILE_DIR
from utils.helpers import comid_to_class
from utils.alteration_assessment import assess_alteration
from classes.UserUploadedData import UserUploadedData
import os
import boto3
from botocore.exceptions import ClientError
import os
import warnings
import py7zr
import pandas as pd


import os
import pandas as pd
from pathlib import Path

def process_parquet_files():
    parquet_gauges = []
    input_path = Path(INPUT_FILE_DIR)
    output_path = Path(INPUT_FILE_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    for parquet_file in input_path.glob("*.parquet"):
        gauge_list = []

        print(f"Processing {parquet_file}...")
        try:
            df = pd.read_parquet(parquet_file)
        except Exception as e:
            print(f"Error reading {parquet_file}: {e}")
            continue

        if 'comId' not in df.index.names:
            print(f"Column 'comId' not found in {parquet_file}'s indices. Skipping file.")
            continue
        df = df['discharge_q0.5']
        df = df.reset_index()
        df = df.rename(columns={"discharge_q0.5": "flow","datetime": "date"})

        for value, group in df.groupby('comId'):
            csv_filename = f"{value}.csv"
            csv_filepath = output_path / csv_filename

            try:
                group.to_csv(csv_filepath, index=False)
                print(f"Written {csv_filepath}")

            except Exception as e:
                print(f"Error writing {csv_filepath}: {e}")
            gage_obj = UserUploadedData(file_name=value, comid = value, download_directory=csv_filepath)
            gage_obj.flow_class = comid_to_class(gage_obj.comid)
            if not gage_obj.flow_class:
                print(f'{value} has no flow class! Defaulting...')
                gage_obj.flow_class = CLASS_TO_NUMBER['NA']
            gauge_list.append(gage_obj)
        parquet_gauges.append(gauge_list)
    return parquet_gauges

def main():

    parquet_file_dirs = process_parquet_files()
    for gauges in parquet_file_dirs:
        print("Beginning flow metric calculation for parquet file")
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')

            dir_name = f'Combined_{str(gauges[0].comid)[:4]}'

            output_files_dir = os.path.join(OUTPUT_FILE_DIR,dir_name)
            print(output_files_dir)
            if not os.path.exists(output_files_dir):
                os.mkdir(output_files_dir)
            alteration_files, upload_warning = upload_files(start_date = WY_START_DATE, gage_arr = gauges, output_files = output_files_dir, batched = True, alteration_needed=True)
        print("Beginning  to assess alteration for parquet file")
        warning_message = assess_alteration(gauges, alteration_files, output_files = output_files_dir, aa_start_year=None, aa_end_year=None, wyt_list = ['any', 'wet', 'dry', 'moderate'])
        for alteration_file in alteration_files:
            print(f'Removing: {alteration_file}')
            if DELETE_INDIVIDUAL_FILES_WHEN_BATCH and os.path.isfile(alteration_file):
                os.remove(alteration_file)

        with py7zr.SevenZipFile(f'{str(gauges[0].comid)[:4]}.7z', 'w') as archive:
            archive.writeall(output_files_dir, 'base')

        #upload_file(f'{str(gauges[0].comid)[:4]}.7z')



def upload_file(file_name, bucket= 's3://upstream-ffm', object_name=None):
    # Taken from AWS documentation

    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print(e)
        return False
    return True






if __name__ == "__main__":
    main()