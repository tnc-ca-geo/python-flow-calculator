from utils.upload_files import upload_files
from utils.constants import NUMBER_TO_CLASS, VERSION, WY_START_DATE, DELETE_INDIVIDUAL_FILES_WHEN_BATCH, CLASS_TO_NUMBER, QUIT_ON_ERROR, SKIP_PROMPTS_BATCH, REQUIRED_BATCH_COLUMNS, LONGITUDE_COLUMNS
from utils.helpers import comid_to_class
from utils.alteration_assessment import assess_alteration, assess_alteration_by_wyt
from classes.Exceptions.missing_columns import MissingColumnsError
from classes.USGSGage import USGSGage
from classes.Exceptions.not_enough_data import NotEnoughDataError
from classes.UserUploadedData import UserUploadedData
from classes.CDECGage import CDECGage
from datetime import datetime
import os
import glob
import sys
import questionary
import traceback
import re
import time
import threading
import asyncio
import warnings
import csv

input_files = 'user_input_files'
output_files_dir = 'user_output_files'
done = False
gage_arr = []
alterationNeeded = False
wyt_analysis = False
start_date = WY_START_DATE
auto_start = False
aa_start_year = None
aa_end_year = None

def clear_screen():
    # Clear screen using ANSI escape codes
    os.system('cls' if os.name == 'nt' else 'clear') if os.name != 'posix' else os.system('printf "\033c"')

def spinning_bar(string):
    chars = ["|", "/", "-", "\\"]
    index = 0
    while not done:
        print(f"\r{string}{chars[index]}", end="", flush=True)
        index = (index + 1) % len(chars)
        time.sleep(0.1)


if __name__ == '__main__':


    clear_screen()
    questionary.print(f"Functional Flows Calculator", style="fg:green")
    questionary.print(f"Version: {VERSION}",style="fg:blue")
    questionary.press_any_key_to_continue().ask()
    
    alterationNeeded = questionary.confirm("Would you like to perform an alteration assessment in addition to generating metrics?").ask()
    
    if alterationNeeded is None:
        questionary.print("FATAL ERROR: Please provide if you wish for an alteration assessment", style="bold fg:red")
        questionary.print("→ Restart the calculator by running \"python main.py\" ←")
        sys.exit()


    elif alterationNeeded:
        
        wyt_analysis = questionary.confirm("In addition to the default alteration assessment would you like to do an alteration assessment by water year type?").ask()
        year_range = questionary.confirm("Would you like to limit the year range of data used for the alteration assessment?").ask()
        
        if year_range:
            aa_start_year = questionary.text(f'Please enter the start year for alteration assessment',
                                        validate = lambda year: True if bool(re.match(r'^[12][0-9]{3}$', year)) else "Please enter a valid start year (YYYY)").ask()
            aa_end_year = questionary.text(f'Please enter the end year for alteration assessment',
                                        validate = lambda year: True if bool(re.match(r'^[12][0-9]{3}$', year)) else "Please enter a valid end year (YYYY)").ask()
            if int(aa_start_year) > int(aa_end_year):
                questionary.print("FATAL ERROR: Start year must become before end year", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()
            
            aa_start_year = int(aa_start_year)
            aa_end_year = int(aa_end_year)
            

    input_method = questionary.select(

                f"Would you like to upload a formatted batch csv or fill in information in questionnaire mode?",

                choices=[
                    'Questionnaire',
                    'Batch CSV'         
                ]).ask()
    
    if input_method is None:
        questionary.print("FATAL ERROR: Please provide what input method you wish to use", style="bold fg:red")
        questionary.print("→ Restart the calculator by running \"python main.py\" ←")
        sys.exit()
    elif input_method == 'Batch CSV':
            questionary.print(f"Please ensure your batch processing CSV is in the directory {input_files} and follows the formatting guide in the README")
            questionary.press_any_key_to_continue().ask()
            csv_files = glob.glob1(input_files, '*.csv')
            user_uploaded_parse_warning = ''
            usgs_parse_warning = ''
            cdec_parse_warning = ''
            if not csv_files:
                questionary.print("FATAL ERROR: No CSV files found", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit(f"Please ensure your batch processing CSV is in {input_files} and has the .csv file extension then try again")

            selected_file = questionary.select(

                'What file would you like to use?',

                choices=csv_files).ask()
            
            if selected_file is None:
                questionary.print("FATAL ERROR: Please select a file you would like to use", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()
            
            cdec_to_be_downloaded = []
            usgs_to_be_downloaded = []
            done = False
            csv_thread = threading.Thread(target=spinning_bar, args= ('Processing CSV... ',))
            csv_thread.start()
            file_path = os.path.join(input_files, selected_file)
            try:
                with open(file_path, 'r') as file:
                    reader = csv.DictReader(file)
                    csv_columns = reader.fieldnames
                    missing_columns = [col for col in REQUIRED_BATCH_COLUMNS if col not in csv_columns]
                    if not (set(csv_columns) & set(LONGITUDE_COLUMNS)):
                        # ensuring that these have a set intersection (there is atleast one of 'lon' or 'lat' in the columns)
                        missing_columns.append('lng')
                    if missing_columns:
                        raise MissingColumnsError('batch csv missing columns', missing_columns)
                    for line in reader:
                        line_gage_obj = ''
                        if 'lng' in line.keys():
                            longitude_column = 'lng'
                        else:
                            longitude_column = 'lon'
                        # if any pair of 2 exist error out (also captures the all 3 case)
                        if ((line['usgs'] != '') and (line['cdec'] != '')) or ((line['usgs'] != '') and (line['path'] != '')) or ((line['cdec'] != '') and (line['path'] != '')):
                                done = True
                                if 'csv_thread' in locals():
                                    csv_thread.join()
                                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                                questionary.print(f"Error: Please only include one of usgs, path or cdec \n The line that failed looks like: \n\tusgs: {line['usgs']}\n\tcdec: {line['cdec']}\n\tpath: {line['path']}\n\tcalculator: {line['calculator']}", style="bold fg:red")
                                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                                sys.exit()
                        
                        selected_calculator = line['calculator'].lower()
                        if selected_calculator == '':
                            selected_calculator = None
                        if not (selected_calculator == 'flashy' or selected_calculator == 'reference' or selected_calculator == '' or selected_calculator == None):
                            done = True
                            if 'csv_thread' in locals():
                                csv_thread.join()
                            sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                            questionary.print(f"Error: 'calculator' field must be Flashy, Reference or blank for all rows\n The line that failed looks like: \n\tusgs: {line['usgs']}\n\tcdec: {line['cdec']}\n\tpath: {line['path']}\n\tcalculator: {line['calculator']}", style="bold fg:red")
                            questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                            sys.exit()
                        
                        if line['usgs'] != '':
                            usgs_to_be_downloaded.append({'id': line['usgs'], 'comid': line['comid'], 'class': line['class'], 'calc': selected_calculator})
                        elif line['cdec'] != '':
                            cdec_to_be_downloaded.append({'id': line['cdec'].upper(), 'comid': line['comid'], 'class': line['class'], 'calc': selected_calculator})
                        elif line['path'] != '':
                            file_name = os.path.splitext(os.path.basename(line['path']))[0]
                            
                            if line['comid'] != '':
                                line_gage_obj = UserUploadedData(file_name=file_name, comid = line['comid'], download_directory=line['path'], selected_calculator=selected_calculator)

                            elif (line['lat'] != '') and (line[longitude_column] != ''):
                                
                                line_gage_obj = UserUploadedData(file_name=file_name, longitude = line[longitude_column], latitude = line['lat'], download_directory=line['path'],  selected_calculator=selected_calculator)
                                line_gage_obj.get_comid()

                            else:
                                line_gage_obj = UserUploadedData(file_name=file_name, download_directory=line['path'])
                            
                            line_gage_obj.flow_class = line['class']
                            if line_gage_obj.flow_class == '' and line_gage_obj.comid is not None and line_gage_obj.comid != '':
                                line_gage_obj.flow_class = comid_to_class(line_gage_obj.comid) 
                            elif line_gage_obj.flow_class != '':
                                line_gage_obj.flow_class = CLASS_TO_NUMBER[line['class'].upper()]
                            if (line_gage_obj.flow_class is None) or (line_gage_obj.flow_class == ''):
                                line_gage_obj.flow_class = CLASS_TO_NUMBER['NA']
                                user_uploaded_parse_warning = user_uploaded_parse_warning + f'Could not auto populate stream class for file {line["path"]} proceeding using default stream class\n'
                            
                            gage_arr.append(line_gage_obj)

                        else:
                            done = True
                            if 'csv_thread' in locals():
                                csv_thread.join()
                            sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                            questionary.print("FATAL ERROR: all batch csv lines must have a path, USGS ID or a CDEC ID provided", style="bold fg:red")
                            questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                            sys.exit()
            except MissingColumnsError as e:
                done = True
                if 'csv_thread' in locals():
                    csv_thread.join()
                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                REQUIRED_BATCH_COLUMNS.insert(6,'lng')
                questionary.print(f"FATAL ERROR: Supplied batch csv: {file_path} is malformed, expected: {REQUIRED_BATCH_COLUMNS} columns but was missing: {e.missing_columns}", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()
            
            except PermissionError:
                done = True
                if 'csv_thread' in locals():
                    csv_thread.join()
                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                questionary.print(f"FATAL ERROR: No permissions to read from file: {file_path}, please supply read access and run again", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()

            except FileNotFoundError:
                done = True
                if 'csv_thread' in locals():
                    csv_thread.join()
                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                questionary.print(f"FATAL ERROR: Unable to find file {file_path}", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()

            except KeyError:    
                done = True
                if 'csv_thread' in locals():
                    csv_thread.join()
                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                keys_str = ', '.join(CLASS_TO_NUMBER.keys())
                questionary.print(f"FATAL ERROR: while parsing file {line['path']}'s stream class: {line['class']} is not a valid class, please supply one of {keys_str} or leave it blank", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()
             
            except Exception as e:
                done = True
                if 'csv_thread' in locals():
                    csv_thread.join()
                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                questionary.print(traceback.format_exc())
                questionary.print("FATAL ERROR parsing selected csv, please ensure it is formatted correctly see error message above", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()
                
            done = True
            if 'csv_thread' in locals():
                    csv_thread.join()
            sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
            questionary.print("Processing CSV... Complete", style="bold fg:green")

            if user_uploaded_parse_warning:
                questionary.print('\nWarnings encountered while parsing user supplied timeseries data:', style='fg:#deda03')
                questionary.print(user_uploaded_parse_warning)
            if len(usgs_to_be_downloaded) > 0:

                for usgs_dict in usgs_to_be_downloaded:
                    
                    try:
                        done = False
                        usgs_string = f'Downloading and parsing USGS metadata for gage: {usgs_dict["id"]}... '
                        usgs_dl_thread = threading.Thread(target=spinning_bar, args= (usgs_string,))
                        usgs_dl_thread.start()
                        if len(usgs_dict['id']) < 8:
                            original_id = usgs_dict['id'] 
                            usgs_dict['id'] = usgs_dict['id'].zfill(8)
                            usgs_parse_warning = usgs_parse_warning + f'USGS id: {original_id} was less than 8 characters and has been buffered with zeroes to make it 8 characters: {usgs_dict["id"]} \n'
                        new_gage = USGSGage(gage_id = usgs_dict['id'])
                        start = time.time()
                        new_gage.download_metadata()
                        new_gage.selected_calculator = usgs_dict['calc']
                        new_gage.comid = usgs_dict['comid']
                        comid = new_gage.get_comid() 
                        new_gage.flow_class = usgs_dict['class']
                        if new_gage.flow_class == '':
                            new_gage.flow_class = comid_to_class(new_gage.comid)
                        else:
                            new_gage.flow_class = CLASS_TO_NUMBER[usgs_dict['class'].upper()]
                        if (new_gage.flow_class is None) or (new_gage.flow_class == ''):
                            new_gage.flow_class = CLASS_TO_NUMBER['NA']
                            usgs_parse_warning = usgs_parse_warning + f'Could not auto populate stream class for gage: {usgs_dict["id"]}, proceeding using the default stream class\n'
                            
                        gage_arr.append(new_gage)
                        time_elapsed =  time.time() - start
                        time_elapsed = round(time_elapsed,2)
                        done = True
                        if 'usgs_dl_thread' in locals():
                            usgs_dl_thread.join()
                        sys.stdout.write("\r" + " " * (len(usgs_string) + 1) + "\r")
                        questionary.print(f"{usgs_string}Complete, took {time_elapsed} seconds", style="bold fg:green")
                    
                    except KeyError:    
                        done = True
                        if 'usgs_dl_thread' in locals():
                            usgs_dl_thread.join()
                        sys.stdout.write("\r" + " " * (len(usgs_string) + 1) + "\r")
                        questionary.print(f"{usgs_string}Error", style="bold fg:red")
                        keys_str = ', '.join(CLASS_TO_NUMBER.keys())
                        usgs_parse_warning = usgs_parse_warning + f"Error parsing supplied USGS class for gage id: {usgs_dict['id']}, {usgs_dict['class']} is not a valid class, please supply one of {keys_str}\n"
                        if QUIT_ON_ERROR:
                            questionary.print(traceback.format_exc())
                            sys.exit()
                        else:
                            continue

                    except Exception as e:
                        done = True
                        if 'usgs_dl_thread' in locals():
                            usgs_dl_thread.join()
                        sys.stdout.write("\r" + " " * (len(usgs_string) + 1) + "\r")
                        questionary.print(f"{usgs_string}Error", style="bold fg:red")
                        usgs_parse_warning = usgs_parse_warning + f"Error parsing USGS metadata for gage: {usgs_dict['id']} please ensure it is a real USGS gage, proceeding without it\n"
                        if QUIT_ON_ERROR:
                            questionary.print(traceback.format_exc())
                            sys.exit()
                        else:
                            continue
                
                done = True
                if 'usgs_dl_thread' in locals():
                        usgs_dl_thread.join()
                sys.stdout.write("\r" + " " * (len(usgs_string) + 1) + "\r")

            if usgs_parse_warning:
                questionary.print('\nWarnings encountered while parsing USGS data:', style='fg:#deda03')
                questionary.print(usgs_parse_warning)
            
            asyncio.set_event_loop(asyncio.new_event_loop())
            
            if len(cdec_to_be_downloaded) > 0:
                
                    for cdec_dict in cdec_to_be_downloaded:
                        try:
                            done = False
                            cdec_string = f'Downloading and parsing CDEC metadata for gage: {cdec_dict["id"]}... '
                            cdec_dl_thread = threading.Thread(target=spinning_bar, args= (cdec_string,))
                            cdec_dl_thread.start()
                            new_gage = CDECGage(gage_id = cdec_dict['id'])
                            start = time.time()
                            new_gage.download_metadata()
                            new_gage.selected_calculator = cdec_dict['calc']
                            new_gage.comid = cdec_dict['comid']
                            comid = new_gage.get_comid() 
                            new_gage.flow_class = cdec_dict['class']
                            if new_gage.flow_class == '':
                                new_gage.flow_class = comid_to_class(new_gage.comid)
                            else:
                                new_gage.flow_class = CLASS_TO_NUMBER[cdec_dict['class'].upper()]
                            if (new_gage.flow_class is None) or (new_gage.flow_class == ''):
                                new_gage.flow_class = CLASS_TO_NUMBER['NA']
                                cdec_parse_warning = cdec_parse_warning + f'Could not auto populate stream class for gage: {cdec_dict["id"]} proceeding using the default stream class\n'
                            
                            gage_arr.append(new_gage)
                            time_elapsed =  time.time() - start
                            time_elapsed = round(time_elapsed,2)
                            done = True
                            if 'cdec_dl_thread' in locals():
                                cdec_dl_thread.join()
                            sys.stdout.write("\r" + " " * (len(cdec_string) + 1) + "\r")
                            questionary.print(f"{cdec_string}Complete, took {time_elapsed} seconds", style="bold fg:green")

                        except KeyError:    
                            done = True
                            if 'cdec_dl_thread' in locals():
                                cdec_dl_thread.join()
                            sys.stdout.write("\r" + " " * (len(cdec_string) + 1) + "\r")
                            questionary.print(f"{cdec_string}Error", style="bold fg:red")
                            keys_str = ', '.join(CLASS_TO_NUMBER.keys())
                            cdec_parse_warning = cdec_parse_warning + f"Error parsing supplied USGS class for gage id: {cdec_dict['id']}, {cdec_dict['class']} is not a valid class, please supply one of {keys_str}\n"
                            if QUIT_ON_ERROR:
                                questionary.print(traceback.format_exc())
                                sys.exit()
                            else:
                                continue

                        except Exception as e:
                            done = True
                            if 'cdec_dl_thread' in locals():
                                cdec_dl_thread.join()
                            sys.stdout.write("\r" + " " * (len(cdec_string) + 1) + "\r")
                            questionary.print(f"{cdec_string}Error", style="bold fg:red")
                            cdec_parse_warning = cdec_parse_warning + f"Error scraping CDEC metadata for gage: {cdec_dict['id']} please ensure it is a real CDEC gage, proceeding without it\n"
                            if QUIT_ON_ERROR:
                                questionary.print(traceback.format_exc())
                                sys.exit()
                            else:
                                continue

                    done = True
                    if 'cdec_dl_thread' in locals():
                        cdec_dl_thread.join()
                    sys.stdout.write("\r" + " " * (len(cdec_string) + 1) + "\r")

            if cdec_parse_warning:
                questionary.print('\nWarnings encountered while parsing CDEC data:', style='fg:#deda03')
                questionary.print(cdec_parse_warning)
            
            if (cdec_parse_warning != "" or usgs_parse_warning != "" or user_uploaded_parse_warning != "") and not SKIP_PROMPTS_BATCH:
                # there was a warning
                warnings_list = []
                if usgs_parse_warning:
                    warnings_list.append(f'USGS WARNINGS:\n{usgs_parse_warning}')
                if cdec_parse_warning:
                    warnings_list.append(f'CDEC WARNINGS:\n{cdec_parse_warning}')
                if user_uploaded_parse_warning:
                    warnings_list.append(f'Timeseries Data WARNINGS:\n{user_uploaded_parse_warning}')

                if warnings_list:
                    questionary.print("\n".join(warnings_list), style='fg:#deda03')
                proceed = questionary.confirm("The above warnings ocurred when fetching & processing the required metadata would you like to proceed to downloading the data?").ask()
                if not proceed:
                    questionary.print(f"Please review the batch csv to address the warnings", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()

            gages_with_data = []
            gages_without_data = []
            for gage in gage_arr:
                done = False
                gage_string = f"Downloading flow data for {gage.gage_id}... "
                current_gage_dl_thread = threading.Thread(target=spinning_bar, args= (gage_string,))
                current_gage_dl_thread.start()
                start = time.time()
                
                try:
                    gage.save_daily_data()
                
                except NotEnoughDataError as e:
                    gages_without_data.append(gage)
                    done = True
                    if 'current_gage_dl_thread' in locals():
                        current_gage_dl_thread.join()
                    sys.stdout.write("\r" + " " * (len(gage_string) + 1) + "\r")
                    questionary.print(f"{gage_string}ERROR: Not enough available data", style="bold fg:red")
                    if QUIT_ON_ERROR:
                        questionary.print(traceback.format_exc())
                        sys.exit()
                    else:
                        continue

                except Exception as e:
                    gages_without_data.append(gage)
                    done = True
                    if 'current_gage_dl_thread' in locals():
                        current_gage_dl_thread.join()
                    sys.stdout.write("\r" + " " * (len(gage_string) + 1) + "\r")
                    questionary.print(f"{gage_string}Error", style="bold fg:red")
                    if QUIT_ON_ERROR:
                        questionary.print(traceback.format_exc())
                        sys.exit()
                    else:
                        continue
                
                gages_with_data.append(gage)
                time_elapsed =  time.time() - start
                time_elapsed = round(time_elapsed,2)
                done = True
                if 'current_gage_dl_thread' in locals():
                    current_gage_dl_thread.join()
                sys.stdout.write("\r" + " " * (len(gage_string) + 1) + "\r")
                questionary.print(f"{gage_string}Complete, took {time_elapsed} seconds", style="bold fg:green")
            
            gage_arr = gages_with_data
            if gages_without_data and not SKIP_PROMPTS_BATCH:
                gages_without_data_string = ', '.join([gage.gage_id for gage in gages_without_data])
                proceed = questionary.confirm(f"The following gages had no data or less than a year of data and will not be included in metric calculation in addition to any gages that were excluded earlier:\n{gages_without_data_string}\n Would you like to proceed?").ask()
                if not proceed:
                    questionary.print(f"Please review the above gages that failed to address the missing data", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()
            # skip over the prompts at the end as users that took the time to make a batch csv probably are computing a lot of data and just want to be able to set it and not worry about it until its done 
            auto_start = SKIP_PROMPTS_BATCH
            asyncio.set_event_loop(asyncio.new_event_loop())
    
    
    elif input_method == 'Questionnaire':
        data_type = questionary.select(

            "Would you like to use your own time-series or USGS/CDEC gage data?",

            choices=[

                "Timeseries data",

                "USGS Gage data",

                "CDEC Gage data"

            ]).ask()

        if not data_type:
            questionary.print("FATAL ERROR: No Data type selected", style="bold fg:red")
            questionary.print("→ Restart the calculator by running \"python main.py\" ←")
            sys.exit()
        
        elif data_type == "CDEC Gage data":

            entering = True
            gages_to_be_downloaded = []
            formatted_gages = ""

            while entering:
                gage_id = questionary.text('Please enter a CDEC Gage ID you would like to analyze'
                                        ,validate = lambda id: True if bool(re.match(r'^[a-zA-Z]{3}', id)) else "Please enter a valid CDEC Gage id").ask()
                
                
                if not gage_id:
                    questionary.print("FATAL ERROR No CDEC Gage ID provided", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()
                gage_id = gage_id.upper()
                gages_to_be_downloaded.append(gage_id)
                
                if len(formatted_gages) == 0:
                    formatted_gages = formatted_gages + gage_id
                else:
                    formatted_gages = formatted_gages + ', ' + gage_id
                
                entering = questionary.confirm(f"Current gages: {formatted_gages}\n Would you like to add more gages?").ask()

            questionary.print("This may take a bit, CDEC's API can be slow")
            done = False
            gage_thread = threading.Thread(target=spinning_bar, args= ('Downloading gage data... ',))
            gage_thread.start()
            
            for gage_id in gages_to_be_downloaded:
                
                try:
                    
                    new_gage = CDECGage(gage_id = gage_id)
                    gage_arr.append(new_gage)
                    new_gage.download_metadata()
                    new_gage.save_daily_data()
                    comid = new_gage.get_comid()
                    
                except NotEnoughDataError as e:
                    done = True
                    
                    if 'gage_thread' in locals():
                        gage_thread.join()
                    questionary.print(traceback.format_exc())
                    sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\r" + " " * (len("This may take a bit, CDEC's API can be slow") + 1) + "\r")
                    questionary.print(f"Error: There was some data available for gage {gage_id} but not enough to proceed", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()

                except Exception as e:
                    done = True
                    
                    if 'gage_thread' in locals():
                        gage_thread.join()
                    questionary.print(traceback.format_exc())
                    sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\r" + " " * (len("This may take a bit, CDEC's API can be slow") + 1) + "\r")
                    questionary.print(f"Error downloading gage data for gage: {new_gage} please verify it is a valid CDEC gage id with flow variable availability and try again", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()
            
            done = True
            
            if 'gage_thread' in locals():
                    gage_thread.join()
            sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
            sys.stdout.write("\033[F")
            sys.stdout.write("\r" + " " * (len("This may take a bit, CDEC's API can be slow") + 1) + "\r")
            questionary.print("Downloading gage data... Complete", style="bold fg:green")
            
            # pynhd package kills the asyncio event loop so we need to recreate it before we do more asynchronous questions
            asyncio.set_event_loop(asyncio.new_event_loop())


        elif data_type == "USGS Gage data":
            
            entering = True
            gages_to_be_downloaded = []
            formatted_gages = ""

            while entering:
                gage_id = questionary.text('Please enter a USGS Gage ID you would like to analyze:',
                                        validate = lambda id: True if bool(re.match(r'^[0-9]{7,}$', id)) else "Please enter a valid USGS Gage id").ask()
                
                if not gage_id:
                    questionary.print("FATAL ERROR: No USGS Gage ID provided", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()
                gages_to_be_downloaded.append(gage_id)
                
                if len(formatted_gages) == 0:
                    formatted_gages = formatted_gages + gage_id
                else:
                    formatted_gages = formatted_gages + ', ' + gage_id
                
                entering = questionary.confirm(f"Current gages: {formatted_gages}\n Would you like to add more gages?").ask()

            done = False
            gage_thread = threading.Thread(target=spinning_bar, args= ('Downloading gage data... ',))
            gage_thread.start()
            
            for gage_id in gages_to_be_downloaded:
                
                try:
                    new_gage = USGSGage(gage_id = gage_id.zfill(8))
                    gage_arr.append(new_gage)
                    new_gage.download_metadata()
                    new_gage.save_daily_data()   
                    comid = new_gage.get_comid()


                except NotEnoughDataError as e:
                    done = True
                    
                    if 'gage_thread' in locals():
                        gage_thread.join()
                    sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
                    questionary.print(f"Error: The gage {new_gage} did not have enough data available to continue", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()

                except Exception as e:
                    done = True
                    
                    if 'gage_thread' in locals():
                        gage_thread.join()
                    sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
                    questionary.print(f"Error downloading gage data for gage: {new_gage} please verify it is a valid USGS gage id and try again", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()
            
            done = True
            
            if 'gage_thread' in locals():
                    gage_thread.join()
            sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
            
            questionary.print("Downloading gage data... Complete", style="bold fg:green")
            
            # pynhd package kills the asyncio event loop so we need to recreate it before we do more asynchronous questions with questionary
            asyncio.set_event_loop(asyncio.new_event_loop())

        elif data_type == "Timeseries data":
            questionary.print(f"Please ensure all your desired timeseries csvs are in the directory {input_files} and are correctly formatted")
            questionary.press_any_key_to_continue().ask()
            csv_files = glob.glob1(input_files, '*.csv')
            if not csv_files:
                questionary.print("FATAL ERROR: No CSV files found", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit(f"Please ensure your files are all in {input_files} and have the .csv file extension then run again.")
            
            entering = True
            selected_files = []
            formatted_files = ""
            while entering:
                file_name = questionary.select("Please select a file you would like to use", choices = csv_files).ask()
                
                if not file_name:
                    questionary.print("FATAL ERROR: No file provided", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit()
                selected_files.append(file_name)
                csv_files.remove(file_name)
                if len(formatted_files) == 0:
                    formatted_files = formatted_files + file_name
                else:
                    formatted_files = formatted_files + ', ' + file_name
                
                entering = questionary.confirm(f"Current files: {formatted_files}\n Would you like to add more files?").ask()

            if not selected_files:
                questionary.print("FATAL ERROR: No CSV files selected", style="bold fg:red")
                questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                sys.exit()
            
            for file in selected_files:
                file_path = os.path.join(input_files, file)
                input_type = questionary.select(f"For file {file} would you like to input COMID or a lat long pair to generate predicted metrics used in alteration assessment and to generate water year type"
                                    ,choices=[

                                        "COMID",

                                        "Latitude/Longitude"

                                    ]).ask()
                

                file_name = os.path.splitext(os.path.basename(file))[0]
                if input_type == "COMID":
                    comid_for_file = questionary.text(f'Please enter the COMID associated with file {file}',
                                        validate = lambda id: True if bool(re.match(r'^[0-9]+$', id)) else "Please enter a valid COMID").ask()
                    new_gage = UserUploadedData(file_name=file_name, comid = comid_for_file, download_directory=file_path)
                    gage_arr.append(new_gage)

                elif input_type == "Latitude/Longitude":
                    lat = questionary.text(f'Please enter the Latitude associated with file {file}',
                                        validate = lambda id: True if bool(re.match(r'^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$', id)) else "Please enter a valid Latitude").ask()
                    lng = questionary.text(f'Please enter the Longitude associated with file {file}',
                                        validate = lambda id: True if bool(re.match(r'^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$', id)) else "Please enter a valid Longitude").ask()
                    new_gage = UserUploadedData(file_name=file_name, longitude = lng, latitude = lat, download_directory=file_path)
                    new_gage.get_comid()
                    gage_arr.append(new_gage)
                    new_gage.save_daily_data()

                else:
                    questionary.print("FATAL ERROR: No provided input type", style="bold fg:red")
                    questionary.print("→ Restart the calculator by running \"python main.py\" ←")
                    sys.exit() 

        asyncio.set_event_loop(asyncio.new_event_loop())
        
        # assign flow class
        questionary.print('Populating the stream classes for each gage/timeseries dataset...')
        for gage in gage_arr:
            gage.flow_class = comid_to_class(gage.comid)
            if gage.flow_class is None:
                
                flow_class_mapping = {
                    "Flow Class SM: Snowmelt": CLASS_TO_NUMBER["SM"],
                    "Flow Class HSR: High-volume snowmelt and rain": CLASS_TO_NUMBER["HSR"],
                    "Flow Class LSR: Low-volume snowmelt and rain (default)": CLASS_TO_NUMBER["LSR"],
                    "Flow Class WS: Winter storms": CLASS_TO_NUMBER["WS"],
                    "Flow Class GW: Groundwater": CLASS_TO_NUMBER["GW"],
                    "Flow Class PGR: Perennial groundwater and rain": CLASS_TO_NUMBER["PGR"],
                    "Flow Class FER: Flashy, ephemeral rain": CLASS_TO_NUMBER["FER"],
                    "Flow Class RGW: Rain and seasonal groundwater": CLASS_TO_NUMBER["RGW"],
                    "Flow Class HLP: High elevation low precipitation": CLASS_TO_NUMBER["HLP"]
                }
            
                returned_value = questionary.select(

                    f"What natural flow class best matches {gage.gage_id}? Could not auto populate for comid: {gage.comid}",

                    choices=[

                        "Flow Class SM: Snowmelt",

                        "Flow Class HSR: High-volume snowmelt and rain",

                        "Flow Class LSR: Low-volume snowmelt and rain (default)",

                        "Flow Class WS: Winter storms",

                        "Flow Class GW: Groundwater",

                        "Flow Class PGR: Perennial groundwater and rain",

                        "Flow Class FER: Flashy, ephemeral rain",

                        "Flow Class RGW: Rain and seasonal groundwater",

                        "Flow Class HLP: High elevation low precipitation"

                    ]).ask()
                
                if returned_value:
                    flow_class = flow_class_mapping[returned_value]
                else:
                    flow_class = CLASS_TO_NUMBER["NA"]
                gage.flow_class = flow_class
            selected_calc = questionary.select(f"Which calculator would you like to use for {gage.gage_id}?",
                        choices=[

                        "Recommended calculator based on the supplied/downloaded data",

                        "Reference calculator",

                        "Flashy calculator"
                    ]).ask()
            if selected_calc == "Reference calculator":
                gage.selected_calculator = "Reference"
            elif selected_calc == "Flashy calculator":
                 gage.selected_calculator = "Flashy"
            else:
                gage.selected_calculator = None

    if not auto_start:
        formatted_files = ''
        formatted_stream_classes = ''
        firstGage = True
        for gage in gage_arr:
            gage_file_name = os.path.basename(gage.download_directory)
            calc_string = gage.selected_calculator
            if  calc_string is None:
                calc_string = 'Recommended'
            if firstGage:
                formatted_files = gage_file_name
                formatted_stream_classes = f"    {gage_file_name}:\n        Class: {NUMBER_TO_CLASS[gage.flow_class]}\n        Calculator: {calc_string}"
                firstGage = False
            else:
                formatted_files = formatted_files + ', ' + gage_file_name    
                formatted_stream_classes = formatted_stream_classes + f"\n    {gage_file_name}:\n        Class: {NUMBER_TO_CLASS[gage.flow_class]}\n        Calculator: {calc_string}"
        batch = False
        if len(gage_arr) > 1:
            batch = questionary.confirm('Would you like to batch all your processed metrics into a single file?').ask()
        elif len(gage_arr) <= 0:
            questionary.print("FATAL ERROR: No remaining gages, address the above warnings!", style="bold fg:red")
            questionary.print("→ Restart the calculator by running \"python main.py\" ←")
            sys.exit() 

        ready = questionary.confirm(f"Calculate metrics with the following general parameters?\nFiles:\n    {formatted_files}\nStream Class & Calculator per File:\n{formatted_stream_classes}\nStart Date:\n    {start_date}\nBatched:\n    {batch}\nAlteration Assessment:\n    {alterationNeeded}\n").ask()
        
        if not ready:
            questionary.print("User parameters declined, please review and rerun calculator", style="bold fg:red")
            questionary.print("→ Restart the calculator by running \"python main.py\" ←")
            sys.exit() 
    else:
        batch = True
    
    # make directory for this run to store its files in
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d-%H-%M")
    dir_name = ''
    if len(gage_arr) == 1:
        dir_name = f'{gage_arr[0].gage_id}_{formatted_time}'
        batch = False
    elif len(gage_arr) == 0:
        questionary.print("All gages failed to be populated, no gages left to run metrics on, exiting...", style="bold fg:red")
        questionary.print("→ Restart the calculator by running \"python main.py\" ←")
        sys.exit()
    else:
        dir_name = f'Multiple_{formatted_time}'
    
    output_files_dir = os.path.join(output_files_dir,dir_name)
    if not os.path.exists(output_files_dir):
        os.mkdir(output_files_dir) 
    
    
    try:
        done = False
        upload_warning = ''
        spinner_thread = threading.Thread(target=spinning_bar, args = ('Calculating Metrics... ',))
        spinner_thread.start()
        
        # The reference flow calculator depends on the way certain functions behave when given all nan which causes many warnings
        # Ignoring warnings for now as they are expected eventually these warnings should be addressed by writing wrapper functions
        # These wrapper functions should not change the functionality of the original numpy functions but rather handle the all nan case that is currently throwing warnings more gracefully
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            alteration_files, upload_warning = upload_files(start_date = start_date, gage_arr = gage_arr, output_files = output_files_dir, batched = batch, alteration_needed=alterationNeeded, aa_start_year=aa_start_year, aa_end_year=aa_end_year)
        sys.stdout.write("\r" + " " * (len("Calculating Metrics... ") + 1) + "\r")
    except Exception as e:
        done = True
        if 'spinner_thread' in locals():
            spinner_thread.join()

        sys.stdout.write("\r" + " " * (len("Calculating Metrics... ") + 1) + "\r")
        if upload_warning:
            questionary.print('\nWarnings encountered while computing metrics:', style='fg:#deda03')
            questionary.print(upload_warning)
        questionary.print(traceback.format_exc())
        questionary.print("Error: Metric calculation failed \nSee above error", style="bold fg:red")
        questionary.print("→ Restart the calculator by running \"python main.py\" ←")
        sys.exit()
    
    finally: 
        done = True
        if 'spinner_thread' in locals():
            spinner_thread.join()

    if upload_warning:
        questionary.print('\nWarnings encountered while computing metrics:', style='fg:#deda03')
        questionary.print(upload_warning)
    questionary.print("Calculating Metrics... Complete", style="bold fg:green")
    output_path = os.path.join(output_files_dir, '')
    questionary.print(f"Calculated metrics can be found in {output_path}", style="bold fg:green")
    
    
    if not alterationNeeded:
        questionary.print("Metric calculation completed successfully. Exiting...", style="bold fg:green")
        questionary.print("→ Restart the calculator by running \"python main.py\" ←")
        sys.exit()
    
    try:
        done = False
        alteration_thread= threading.Thread(target=spinning_bar, args = ('Performing Alteration Assessment... ',))
        alteration_thread.start()
        warning_message = assess_alteration(gage_arr, alteration_files, output_files = output_files_dir, aa_start_year=aa_start_year, aa_end_year=aa_end_year)
        if wyt_analysis:
            wyt_warning_message = assess_alteration_by_wyt(gage_arr, alteration_files, output_files = output_files_dir, aa_start_year=aa_start_year, aa_end_year=aa_end_year)
            warning_message =  warning_message + wyt_warning_message
        
        for alteration_file in alteration_files:
            if DELETE_INDIVIDUAL_FILES_WHEN_BATCH and batch and os.path.isfile(alteration_file):
               os.remove(alteration_file)

        sys.stdout.write("\r" + " " * (len("Performing Alteration Assessment... ") + 1) + "\r")
        
    except Exception as e:
        done = True
    
        if 'alteration_thread' in locals():
            alteration_thread.join()

        sys.stdout.write("\r" + " " * (len("Performing Alteration Assessment... ") + 1) + "\r")
        questionary.print(traceback.format_exc())
        questionary.print("Error: Alteration Assessment failed \nSee above error", style="bold fg:red")
        questionary.print("→ Restart the calculator by running \"python main.py\" ←")
        sys.exit()
    
    finally: 
        done = True
        if 'alteration_thread' in locals():
            alteration_thread.join()
    if warning_message:
        questionary.print('\nWarnings encountered while computing alteration assessment:', style='fg:#deda03')
        questionary.print(warning_message)

    questionary.print("Performing Alteration Assessment... Complete", style="bold fg:green")
    questionary.print(f"Alteration Assessment results and associated percentiles can be found in {output_files_dir}/", style="bold fg:green")
    questionary.print("→ Restart the calculator by running \"python main.py\" ←")