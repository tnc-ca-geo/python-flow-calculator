from utils.upload_files import upload_files
from utils.constants import VERSION
from utils.helpers import comid_to_class
from utils.alteration_assessment import assess_alteration, assess_alteration_by_wyt
from classes.USGSGage import USGSGage
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
start_date = '10/1'
auto_start = False

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
    questionary.print(f"Functional Flows Calculator 🏞", style="fg:green")
    questionary.print(f"Version: {VERSION}",style="fg:blue")
    questionary.press_any_key_to_continue().ask()
    
    alterationNeeded = questionary.confirm("Would you like to perform an alteration assessment in addition to generating metrics?").ask()
    
    if alterationNeeded is None:
        questionary.print("🛑 Please provide if you wish for an alteration assessment 🛑", style="bold fg:red")
        sys.exit()

    elif alterationNeeded:
        wyt_analysis = questionary.confirm("In addition to the default alteration assessment would you like to do an alteration assessment by water year type?").ask()

    
    input_method = questionary.select(

                f"Would you like to upload a formatted batch csv or fill in information via CLI",

                choices=[
                    'CLI Questionnaire',
                    'Batch CSV'         
                ]).ask()
    
    if input_method is None:
        questionary.print("🛑 Please provide what input method you wish to use 🛑", style="bold fg:red")
        sys.exit()
    elif input_method == 'Batch CSV':
            questionary.print(f"Please ensure your batch processing CSV is in the directory {input_files} and follows the formatting guide in the README")
            questionary.press_any_key_to_continue().ask()
            csv_files = glob.glob1(input_files, '*.csv')
            
            if not csv_files:
                questionary.print("🛑 No CSV files found 🛑", style="bold fg:red")
                sys.exit(f"Please ensure your batch processing CSV is in {input_files} and has the .csv file extension then try again")

            selected_file = questionary.select(

                'What file would you like to use?',

                choices=csv_files).ask()
            
            if selected_file is None:
                questionary.print("🛑 Please select a file you would like to use 🛑", style="bold fg:red")
                sys.exit()

            start_date = questionary.text('What water-year start date would you like to use m/d?',
                            validate = lambda date: True if bool(re.match(r'^(1[0-2]|0?[1-9])/(3[01]|[12][0-9]|0?[1-9])$', date)) else "Please enter a valid date in m/d format"
                            ).ask()
        
            if not start_date:
                start_date = '10/1'
            
            cdec_to_be_downloaded = []
            usgs_to_be_downloaded = []
            done = False
            csv_thread = threading.Thread(target=spinning_bar, args= ('Processing CSV... ',))
            csv_thread.start()
            file_path = os.path.join(input_files, selected_file)
            try:
                with open(file_path, 'r') as file:
                    reader = csv.DictReader(file)
                    for line in reader:
                        line_gage_obj = ''

                        # if any pair of 2 exist error out (also captures the all 3 case)
                        if ((line['usgs'] != '') and (line['cdec'] != '')) or ((line['usgs'] != '') and (line['path'] != '')) or ((line['cdec'] != '') and (line['path'] != '')):
                                done = True
                                if 'csv_thread' in locals():
                                    csv_thread.join()
                                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                                questionary.print(f"❌ Please only include one of usgs, path or cdec ❌\n The line that failed looks like: \n\tusgs: {line['usgs']}\n\tcdec: {line['cdec']}\n\tpath: {line['path']}", style="bold fg:red")
                                sys.exit()

                        if line['usgs'] != '':
                            usgs_to_be_downloaded.append({'id': line['usgs'], 'comid': line['comid'], 'class': line['class']})
                        elif line['cdec'] != '':
                            cdec_to_be_downloaded.append({'id': line['cdec'], 'comid': line['comid'], 'class': line['class']})
                        elif line['path'] != '':
                            file_name = os.path.splitext(os.path.basename(line['path']))[0]
                            if line['comid'] != '':
                                line_gage_obj = UserUploadedData(file_name=file_name, comid = line['comid'], download_directory=line['path'])

                            elif (line['lat'] != '') and (line['lng'] != ''):
                                line_gage_obj = UserUploadedData(file_name=file_name, longitude = line['lng'], latitude = line['lat'], download_directory=line['path'])
                                line_gage_obj.get_comid()

                            else:
                                done = True
                                if 'csv_thread' in locals():
                                    csv_thread.join()
                                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                                questionary.print("❌ all batch csv lines with a path must also have a lat/lng pair or a comid ❌", style="bold fg:red")
                                sys.exit()
                            
                            line_gage_obj.flow_class = line['class']
                            if line_gage_obj.flow_class == '':
                                line_gage_obj.flow_class = comid_to_class(line_gage_obj.comid) 
                            if (line_gage_obj.flow_class is None) or (line_gage_obj.flow_class == ''):
                                done = True
                                if 'csv_thread' in locals():
                                    csv_thread.join()
                                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                                questionary.print(f"🛑 Could not auto populate flow class for file: {line['path']} and no flow class was supplied in batch csv. 🛑\n🛑 Please supply a flow class for this file or a comid with a known flow class 🛑", style="bold fg:red")            
                                sys.exit()
                            gage_arr.append(line_gage_obj)

                        else:
                            done = True
                            if 'csv_thread' in locals():
                                csv_thread.join()
                            sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                            questionary.print("❌ all batch csv lines must have a path, USGS ID or a CDEC ID ❌", style="bold fg:red")
                            sys.exit()
            except Exception as e:
                done = True
                if 'csv_thread' in locals():
                    csv_thread.join()
                sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
                questionary.print(traceback.format_exc())
                questionary.print("🛑 Error parsing selected csv, please ensure it is formatted correctly see error message above 🛑", style="bold fg:red")
                sys.exit()
                
            done = True
            if 'csv_thread' in locals():
                    csv_thread.join()
            sys.stdout.write("\r" + " " * (len("Processing CSV... ") + 1) + "\r")
            questionary.print("Processing CSV... ✔️", style="bold fg:lightgreen")

            
            if len(usgs_to_be_downloaded) > 0:
                done = False
                usgs_dl_thread = threading.Thread(target=spinning_bar, args= ('Downloading USGS data... ',))
                usgs_dl_thread.start()

                for usgs_dict in usgs_to_be_downloaded:
                    
                    try:
                    
                        new_gage = USGSGage(gage_id = usgs_dict['id'])
                        new_gage.download_metadata()
                        new_gage.save_daily_data()   
                        new_gage.comid = usgs_dict['comid']
                        comid = new_gage.get_comid() 
                        new_gage.flow_class = usgs_dict['class']
                        if new_gage.flow_class == '':
                            new_gage.flow_class = comid_to_class(new_gage.comid)
                        if (new_gage.flow_class is None) or (new_gage.flow_class == ''):
                            done = True
                            if 'usgs_dl_thread' in locals():
                                usgs_dl_thread.join()
                            sys.stdout.write("\r" + " " * (len("Downloading USGS data... ") + 1) + "\r")
                            questionary.print(f"🛑 Could not auto populate flow class for USGS gage: {new_gage.gage_id} and no flow class was supplied in batch csv. 🛑\n🛑 Please supply a flow class for this gage or a comid with a known flow class 🛑", style="bold fg:red")            
                            sys.exit()
                        gage_arr.append(new_gage)
                    
                    except Exception as e:
                        done = True
                        if 'usgs_dl_thread' in locals():
                            usgs_dl_thread.join()
                        sys.stdout.write("\r" + " " * (len("Downloading USGS data... ") + 1) + "\r")
                        questionary.print(traceback.format_exc())
                        questionary.print(f"🛑 Error downloading USGS data for gage id: {usgs_dict['id']} see above traceback 🛑", style="bold fg:red")
                        sys.exit()
                
                done = True
                if 'usgs_dl_thread' in locals():
                        usgs_dl_thread.join()
                sys.stdout.write("\r" + " " * (len("Downloading USGS data... ") + 1) + "\r")
                questionary.print("Downloading USGS data... ✔️", style="bold fg:lightgreen")

            if len(cdec_to_be_downloaded) > 0:
                done = False
                questionary.print("This may take a bit, CDEC's API can be slow")
                cdec_dl_thread = threading.Thread(target=spinning_bar, args= ('Downloading CDEC data... ',))
                cdec_dl_thread.start()
                
                try:
                    for cdec_dict in cdec_to_be_downloaded:

                        new_gage = CDECGage(gage_id = cdec_dict['id'])
                        new_gage.download_metadata()
                        new_gage.save_daily_data()
                        new_gage.comid = cdec_dict['comid']
                        comid = new_gage.get_comid() 
                        new_gage.flow_class = cdec_dict['class']
                        if new_gage.flow_class == '':
                            new_gage.flow_class = comid_to_class(new_gage.comid) 
                        if (new_gage.flow_class is None) or (new_gage.flow_class == ''):
                            done = True
                            if 'cdec_dl_thread' in locals():
                                cdec_dl_thread.join()
                            sys.stdout.write("\r" + " " * (len("Downloading CDEC data... ") + 1) + "\r")
                            questionary.print(f"🛑 Could not auto populate flow class for CDEC gage: {new_gage.gage_id} and no flow class was supplied in batch csv. 🛑\n🛑 Please supply a flow class for this gage or a comid with a known flow class 🛑", style="bold fg:red")            
                            sys.exit()
                        gage_arr.append(new_gage)
                        


                except Exception as e:
                        done = True
                        if 'cdec_dl_thread' in locals():
                            cdec_dl_thread.join()
                        sys.stdout.write("\r" + " " * (len("Downloading CDEC data... ") + 1) + "\r")
                        questionary.print(f"🛑 Error Downloading CDEC data for gage id: {cdec_dict['id']} 🛑", style="bold fg:red")
                        sys.exit()

                done = True
                if 'cdec_dl_thread' in locals():
                        cdec_dl_thread.join()
                sys.stdout.write("\r" + " " * (len("Downloading CDEC data... ") + 1) + "\r")
                sys.stdout.write("\033[F")
                sys.stdout.write("\r" + " " * (len("This may take a bit, CDEC's API can be slow") + 1) + "\r")
                questionary.print("Downloading CDEC data... ✔️", style="bold fg:lightgreen")
            
            # skip over the prompts at the end as users that took the time to make a batch csv probably are computing alot of data and just want to be able to set it and not worry about it until its done 
            auto_start = True
            asyncio.set_event_loop(asyncio.new_event_loop())
    
    
    elif input_method == 'CLI Questionnaire':
        data_type = questionary.select(

            "Would you like to use your own time-series or USGS/CDEC gage data?",

            choices=[

                "Timeseries data",

                "USGS Gage data",

                "CDEC Gage data"

            ]).ask()

        if not data_type:
            questionary.print("🛑 No Data type selected 🛑", style="bold fg:red")
            sys.exit()
        
        elif data_type == "CDEC Gage data":

            entering = True
            gages_to_be_downloaded = []
            formatted_gages = ""

            while entering:
                gage_id = questionary.text('Please enter a CDEC Gage ID you would like to analyze'
                                        ,validate = lambda id: True if bool(re.match(r'^[A-Z]{3}', id)) else "Please enter a valid CDEC Gage id").ask()
                
                if not gage_id:
                    questionary.print("🛑 No CDEC Gage ID provided 🛑", style="bold fg:red")
                    sys.exit()
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
                    

                except Exception as e:
                    done = True
                    
                    if 'gage_thread' in locals():
                        gage_thread.join()
                    print(e)
                    sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\r" + " " * (len("This may take a bit, CDEC's API can be slow") + 1) + "\r")
                    questionary.print(f"🛑 Error downloading gage data for gage: {new_gage} please verify it is a valid CDEC gage id with flow variable availability and try again 🛑", style="bold fg:red")
                    sys.exit()
            
            done = True
            
            if 'gage_thread' in locals():
                    gage_thread.join()
            sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
            sys.stdout.write("\033[F")
            sys.stdout.write("\r" + " " * (len("This may take a bit, CDEC's API can be slow") + 1) + "\r")
            questionary.print("Downloading gage data... ✔️", style="bold fg:lightgreen")
            
            # pynhd package kills the asyncio event loop for some reason so need to recreate it before we do more asynchronous questions
            asyncio.set_event_loop(asyncio.new_event_loop())


        elif data_type == "USGS Gage data":
            
            entering = True
            gages_to_be_downloaded = []
            formatted_gages = ""

            while entering:
                gage_id = questionary.text('Please enter a USGS Gage ID you would like to analyze:',
                                        validate = lambda id: True if bool(re.match(r'^[0-9]{8,}$', id)) else "Please enter a valid USGS Gage id").ask()
                
                if not gage_id:
                    questionary.print("🛑 No USGS Gage ID provided 🛑", style="bold fg:red")
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
                    
                    new_gage = USGSGage(gage_id = gage_id)
                    gage_arr.append(new_gage)
                    new_gage.download_metadata()
                    new_gage.save_daily_data()   
                    comid = new_gage.get_comid()

                except Exception as e:
                    done = True
                    
                    if 'gage_thread' in locals():
                        gage_thread.join()
                    
                    questionary.print(f"🛑 Error downloading gage data for gage: {new_gage} please verify it is a valid USGS gage id and try again 🛑", style="bold fg:red")
                    sys.exit()
            
            done = True
            
            if 'gage_thread' in locals():
                    gage_thread.join()
            sys.stdout.write("\r" + " " * (len("Downloading gage data... ") + 1) + "\r")
            
            questionary.print("Downloading gage data... ✔️", style="bold fg:lightgreen")
            
            # pynhd package kills the asyncio event loop so need to recreate it before we do more asyncronous questions with questionairy
            asyncio.set_event_loop(asyncio.new_event_loop())

        elif data_type == "Timeseries data":
            questionary.print(f"Please ensure all your desired timeseries csvs are in the directory {input_files} and are correctly formatted")
            questionary.press_any_key_to_continue().ask()
            csv_files = glob.glob1(input_files, '*.csv')
            if not csv_files:
                questionary.print("🛑 No CSV files found 🛑", style="bold fg:red")
                sys.exit(f"Please ensure your files are all in {input_files} and have the .csv file extension then run again.")

            selected_files = questionary.checkbox(

                'What files would you like to upload?',

                choices=csv_files).ask()

            if not selected_files:
                questionary.print("🛑 No CSV files selected 🛑", style="bold fg:red")
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

                else:
                    questionary.print("🛑 No provided 🛑", style="bold fg:red")
                    sys.exit() 

        asyncio.set_event_loop(asyncio.new_event_loop())
        
        # assign flow class
        questionary.print('Populating the stream classes for each gage/timeseries dataset...')
        for gage in gage_arr:
            gage.flow_class = comid_to_class(gage.comid)
            if gage.flow_class is None:
                flow_class = questionary.select(

                    f"What natural flow class best matches {gage.gage_id}? Could not auto populate for comid: {gage.comid}",

                    choices=[

                        "Flow Class 1",

                        "Flow Class 2",

                        "Flow Class 3",

                        "Flow Class 4",

                        "Flow Class 5",

                        "Flow Class 6",

                        "Flow Class 7",

                        "Flow Class 8",

                        "Flow Class 9"

                    ]).ask()

                if flow_class:
                    flow_class = int(flow_class[-1:])
                    gage.flow_class = flow_class
                else:
                    questionary.print("🛑 No flow class selected 🛑", style="bold fg:red")
                    sys.exit()
    
        start_date = questionary.text('Start Date of each water year m/d?',
                            validate = lambda date: True if bool(re.match(r'^(1[0-2]|0?[1-9])/(3[01]|[12][0-9]|0?[1-9])$', date)) else "Please enter a valid date in m/d format"
                            ).ask()
        
        if not start_date:
            start_date = '10/1'
    if not auto_start:
        formatted_files = ''
        firstGage = True
        for gage in gage_arr:
            gage_file_name = os.path.basename(gage.download_directory)
            if firstGage:
                formatted_files = gage_file_name
                firstGage = False
            else:
                formatted_files = formatted_files + ', ' + gage_file_name    

        batch = False
        if len(gage_arr) > 1:
            batch = questionary.confirm('Would you like to batch all your processed metrics into a single file?').ask()

        ready = questionary.confirm(f"Calculate metrics with the following general parameters?\nFiles:\n    {formatted_files}\nStart Date:\n    {start_date}\nBatched:\n    {batch}\nAlteration Assessment:\n    {alterationNeeded}\n").ask()
        
        if not ready:
            questionary.print("🛑 User parameters declined 🛑", style="bold fg:red")
            sys.exit() 
    else:
        batch = True
    
    # make directory for this run to store its files in
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d-%H:%M")
    dir_name = ''
    if len(gage_arr) == 1:
        dir_name = f'{gage_arr[0].gage_id}_{formatted_time}' 
    else:
        dir_name = f'Multiple_{formatted_time}'
    
    output_files_dir = os.path.join(output_files_dir,dir_name)
    if not os.path.exists(output_files_dir):
        os.mkdir(output_files_dir) 
    
    
    try:
        done = False
        spinner_thread = threading.Thread(target=spinning_bar, args = ('Calculating Metrics... ',))
        spinner_thread.start()
        
        # The original flow calculator depends on the way certain functions behave when given all nan which causes many warnings
        # Ignoring warnings for now as they are expected eventually these warnings should be addressed by writing wrapper functions
        # These wrapper functions should not change the functionality of the original numpy functions but rather handle the ll nan case that is currently throwing warnings more gracefully
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            alteration_files = upload_files(start_date = start_date, gage_arr = gage_arr, output_files = output_files_dir, batched = batch)
        sys.stdout.write("\r" + " " * (len("Calculating Metrics... ") + 1) + "\r")
    except Exception as e:
        done = True
        if 'spinner_thread' in locals():
            spinner_thread.join()

        sys.stdout.write("\r" + " " * (len("Calculating Metrics... ") + 1) + "\r")
        questionary.print(traceback.format_exc())
        questionary.print("Metric calculation failed ❌\nSee above error ❌", style="bold fg:red")
        sys.exit()
    
    finally: 
        done = True
        if 'spinner_thread' in locals():
            spinner_thread.join()

    questionary.print("Calculating Metrics... ✔️", style="bold fg:lightgreen")
    questionary.print(f"Calculated metrics can be found in {output_files_dir}/", style="bold fg:lightgreen")
    
    
    if not alterationNeeded:
        questionary.print("Metric calculation completed successfully. Exiting...", style="bold fg:lightgreen")
        sys.exit()
    
    try:
        done = False
        alteration_thread= threading.Thread(target=spinning_bar, args = ('Performing Alteration Assessment... ',))
        alteration_thread.start()
        warning_message = assess_alteration(gage_arr, alteration_files, output_files = output_files_dir)
        if wyt_analysis:
            wyt_warning_message = assess_alteration_by_wyt(gage_arr, alteration_files, output_files = output_files_dir)
            warning_message =  warning_message + wyt_warning_message
    
        sys.stdout.write("\r" + " " * (len("Performing Alteration Assessment... ") + 1) + "\r")
        
    except Exception as e:
        done = True
    
        if 'alteration_thread' in locals():
            alteration_thread.join()

        sys.stdout.write("\r" + " " * (len("Performing Alteration Assessment... ") + 1) + "\r")
        questionary.print(traceback.format_exc())
        questionary.print("Alteration Assessment failed ❌\nSee above error ❌", style="bold fg:red")
        sys.exit()
    
    finally: 
        done = True
        if 'alteration_thread' in locals():
            alteration_thread.join()
    if warning_message:
        questionary.print('\nWarnings encountered while computing alteration assessment ⚠️', style='fg:#deda03')
        questionary.print(warning_message)

    questionary.print("Performing Alteration Assessment... ✔️", style="bold fg:lightgreen")
    questionary.print(f"Alteration Assessment results and associated percentiles can be found in {output_files_dir}/", style="bold fg:lightgreen")