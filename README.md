# Functional Flows Calculator

## Table of Contents

1. [About](#about)
2. [Getting Started](#getting-started)
   - [Getting Started (Windows)](#getting-started-windows)
   - [Getting Started (MacOS)](#getting-started-macos)
3. [Using the Calculator](#using-the-calculator)
4. [Supported Data & Modes of Use](#supported-data--modes-of-use)
   - [Data Sources](#data-sources)
   - [Questionnaire Mode](#questionnaire-mode)
   - [Batch CSV Mode](#batch-csv-mode)
     - [Formatting the CSV](#formatting-the-csv)
   - [Alteration Assessments](#alteration-assessments)
5. [Testing](#testing)
6. [Questions and Comments](#questions-and-comments)
   - [Extra info](#extra-info)

## About

This is a remastered functional flow calculator a majority of the logic has been left unchanged but lots of new functionality has been added. The repository has been refactored to be more maintainable and the dependencies have all been updated. Sourced from the [original reference functional flows calculator](https://github.com/leogoesger/func-flow). Additional functionality has been implemented from [the ffc api client](https://github.com/ceff-tech/ffc_api_client) and [the flashy functional flow calculator](https://github.com/camcarpenter6/Alternate-Ruleset-FFC-BETA). As well as some [new low flow metrics](https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2023WR035768) which have an R implementation [here](https://github.com/jessayers20/Functional-Low-Flows). It is still in active development so please report any bugs you find!

## Getting Started

Below is a list of steps for different operating systems to get a working environment to run the flow calculator in. If you are already familiar with cloning repositories and installing dependencies from a requirements.txt file you can skip this section and set up your environment in whatever way you prefer. The only requirement needed that is not within the requirements.txt file is [GDAL](https://gdal.org/).

## Getting Started (Windows)

1. Install [Git](https://git-scm.com/download/) and [Miniconda](https://docs.anaconda.com/free/miniconda/). Most likely you will need the 64 bit windows installers!

2. Create the directory you would like to have the flow calculator in using file explorer and copy the **full** path to that directory.

3. Use the following to open a conda command shell instance in your new directory:
   - In the search bar at the bottom left of your desktop search `Anaconda Prompt (miniconda3)`
   - Run `Anaconda Prompt (miniconda3)`
   - Inside the command shell instance that just opened up type `cd <path-to-directory>` replacing `<path-to-directory>` with the directory path you copied in step 2

4. Clone this repository and change your command shell's window to be within the cloned repository by using:
   - first `git clone https://github.com/tnc-ca-geo/python-flow-calculator.git`
   - second `cd python-flow-calculator`

5. Now create a conda environment and install all the dependencies into it using `conda env create -f environment.yaml`

6. Activate the environment with `conda activate flow-calculator-env`

7. Once you are done using the flow calculator deactivate the environment using `conda deactivate`. Make sure to activate it again before you use the flow calculator the next time!

It should be noted that you only need to use `Anaconda Prompt (miniconda)` because by default conda does not modify PATH variables on Windows. If you would like to set up conda to work outside of Anaconda Prompt (miniconda) and within your normal powershell or command shell you need to [modify your path variables to include conda](https://www.geeksforgeeks.org/how-to-setup-anaconda-path-to-environment-variable/).

## Getting Started (MacOS)

1. Install [Git](https://git-scm.com/download/) and [Miniconda](https://docs.anaconda.com/free/miniconda/)

2. Create and copy the path to the folder you would like to store the functional flows calculator in.

3. In the Finder application, open the `/Applications/Utilities` folder, then double-click Terminal.

4. Within Terminal use cd `cd <path-to-directory>`  replacing `<path-to-directory>` with the directory path you copied in step 2

5. Clone this repository and change your command shell's window to be within the cloned repository by using:
   - First `git clone https://github.com/tnc-ca-geo/python-flow-calculator.git`
   - Second `cd python-flow-calculator`

6. Now create a conda environment and install all the dependencies into it using `conda env create -f environment.yaml`

7. Once you are done using the flow calculator deactivate the environment using `conda deactivate`. Make sure to activate it again before you use the flow calculator the next time!

## Using the Calculator

1. Activate the conda environment made in the "[Getting Started](#getting-started)" section with `conda activate flow-calculator-env`

2. Optionally modify some of the params in the `params.py` file.

3. Simply run

   ``` bash
   python main.py
   ```

   and follow prompts provided to you via the command line interface.

See below for more information on what data you might want to give it.

## Supported Data & Modes of Use

   There are two main modes of usage for the calculator. Firstly there is the questionnaire, this mode is intended for more casual use. It will ask you a series of questions about the data you are trying to calculate metrics on. Secondly there is the batch processing csv mode. This mode is intended for users who want to process large amounts of data from many data sources and don't want to spend the time entering answers for every data source. More in-depth descriptions of how to use each mode can be found below.

### Data Sources

   Currently there are 3 supported data sources for the functional flows calculator:

   1. [USGS](https://www.usgs.gov/) gage data downloaded using the [dataretrieval-python](https://github.com/DOI-USGS/dataretrieval-python) package developed by USGS. This API is very speedy and seems well supported! Currently only [parameter id 00060](https://help.waterdata.usgs.gov/parameter_cd?group_cd=PHY) is supported (discharge in cf/s). A couple example gage ids are 11274500 and 11522500 if you wish to test it out.  
   2. [CDEC](http://cdec.water.ca.gov/) gage data downloaded using the CDEC API. Note that this api is not documented anywhere and is very slow. Currently only parameter ids 20, 41 and 165 (discharge) are supported. Where possible use USGS gage data or take the files downloaded by the flow calculator on the first go through and use them as user uploaded data to save time. Data is downloaded to the /gage_data directory if you wish to view it after the flow calculator runs. A couple example gage ID's are 'NRN' and 'LCH' if you wish to test it out.
   3. User uploaded data. If you have a csv of observations or data from a different data source that is not supported it can be accepted. Ensure all CSVs to be uploaded have a column labeled `flow` and a column labeled `date` it is fine if more columns exist but those two must as they are used as the observations of discharge in cf/s at the given date. If you plan on using Questionnaire mode please ensure your formatted csv files are all in `user_input_files/`. An example file is located at `user_input_files/example_input.csv`

### Questionnaire Mode

   In this mode you will be asked a bunch of questions about each file you want to upload or gage data you want to analyze. It is recommended for poking around or quickly checking things. For large amounts of processing it will be very tedious to use. You will be locked to just one of the three supported data sources when using this mode at a time.

### Batch CSV Mode

   In this mode your input will be read from a specifically formatted csv file. You will be asked a few general questions at the start of the calculator including: if you want an alteration assessment or not and what water year start date applies to the data you would like to analyze.

   After entering this information it will automatically proceed calculating for all the data supplied in the batch csv. This is done so users with an exceptionally large amount of data don't need to wait for all the csvs to download then confirm before the calculations start.

#### Formatting the CSV

   The batch processing csv needs the following column headers (case sensitive) to work: `usgs`, `cdec`, `path`, `comid`, `class`, `lat`, `lng`, `calculator`. More columns can exist but those ones are required and any other columns will be ignored by the calculator. Every row in the csv must have data entered in one and only one of the following columns: `usgs`, `cdec` or `path`. This is the minimum data needed for the calculator to fetch the streamflow data needed to run. If you are providing streamflow data in a file, enter the path to the file in the `path` column, and then fill out at least one of the following columns or columns groups: `comid`, `class` or `lat` AND `lng` for the best results. If you decide to leave these columns blank the calculator will still be able to run but it is not recommended as the calculator will use the default flow class which may produce inaccurate results for the supplied data.

   `usgs`: the `usgs` column is expected to be a USGS gage id often this is a 10 digit number such as 11023250 (see [the Data Sources section](#data-sources) above for more detail). This information will be used to fetch flow data from the USGS API.

   `cdec`: the `cdec` column is expected to be a CDEC gage id often this is a 3 character string such as "SFH" (see [the Data Sources section](#data-sources) above for more detail). This information will be used to fetch flow data from the CDEC API.

   `path`: the `path` column is expected to be a file path to user provided flow data (see [the Data Sources section](#data-sources) above for more information on how). `path` can be a file path to the file relative to the root of this repository or a total path on your machine. This information will be used to fetch flow data from a file on your computer!

   `class`: the `class` column if provided is expected to be the stream classification from one of the following nine options: 'SM', 'HSR', 'LSR', 'WS', 'GW', 'PGR', 'FER', 'RGW', 'HLP'  that matches the classification of your data. More information on the different stream classes can be found at the [*eFlows website*](https://eflows.ucdavis.edu/hydrology)*Note this website has not been available recently*. This information is used to determine what set of parameters to use to calculate metrics on the supplied data. If this column does not have data and cannot be inferred from the below columns the default flow class will be used ("LSR").

   `comid`: the `comid` column if provided is expected to be a COMID sourced from the [NHDPlusV2 dataset](https://www.epa.gov/waterdata/get-nhdplus-national-hydrography-dataset-plus-data) that your selected gage/user uploaded flow data samples from. This column is particularly important when doing alteration assessments as the expected metrics to be compared against are precalculated per-comid in [the natural flows database](https://rivers.codefornature.org/#/home). This information will additionally be used to look up stream class of the supplied data using the file `extra_info/comid_to_stream_class.csv` if the `class` column was not already populated above. Lastly this information is used to find the water year type for each year in the supplied data more information on this in the [Alteration Assessments](#alteration-assessments) section.

   `lat` & `lng`: the `lat` & `lng` columns if provided are expected to be the latitude & longitude pair that represent the point of the gage or where the user uploaded data was obtained in EPSG:4326. This information will be used to "snap" to the closest stream and fetch its comid using [the pyNHD package](https://github.com/hyriver/pynhd). This comid information is then used in place of the `comid` field if its not populated which is then inturn used to populate the `class` field if its not populated.

   `calculator`: the `calculator`column if provided must be either "Flashy" or "Reference". Supplying "Flashy" will make that dataset's functional flow metrics be calculated using a translated version of the [UCDavis flashy calculator](https://github.com/camcarpenter6/Alternate-Ruleset-FFC-BETA) whereas "Reference" will make that dataset's functional flow metrics be calculated using an updated version of [the reference functional flows calculator](https://github.com/leogoesger/func-flow). Leaving the field blank will let the program determine which calculator will produce the best results for your data by using the nature of your input data, the flow class and the metrics produced by the Reference calculator. It is recommended to leave this field blank in almost all cases.

   To run, the calculator needs information on the stream class of the data or it will assume the data belongs to the "LSR" class. A few of the methods the calculator can use to get this information has been detailed above (using columns supplied by the user). There are a couple other methods the calculator can use to populate this data if it is missing and the user is using gage data (supplied by the `usgs` column or the `cdec` column rather then the `path` column). The first option is to use file `extra_info/filtered_stream_gages_v3c_20240311.csv` which contains many gages and their associated comid's to lookup the comid and then use the comid to get the stream class using the `extra_info/comid_to_stream_class.csv` file. If the gage cannot be found within the `extra_info/filtered_stream_gages_v3c_20240311.csv` file then the metadata for the gage will be downloaded or scraped to obtain the latitude and longitude of the gage which will be used as above in the `lat` & `lng` section to obtain the stream class.

   You can see an example batch csv in `batch_example.csv` with some dummy numbers. It covers many of the different cases mentioned above. Feel free to use it and see how the batch processing functionality works before making your own csv.

### Alteration Assessments

   Alteration assessments are one of the core functionalities imported from [the ffc api client](https://github.com/ceff-tech/ffc_api_client). They are done by taking the observed functional flows computed from your data and comparing them with expected natural functional flow metrics retrieved via [the Code for Nature natural flow metrics api](https://rivers.codefornature.org/#/data) using your comid as the key. If one or more of your supplied comid's (either auto populated or manually supplied) does not exist in the Code For Nature database you will get a warning in the command line interface but all of the remaining locations will still have their alteration assessed.

   In addition to a default alteration assessment there is also the possibility to do a alteration assessment by water year type. For this to be possible your comid must be found within the `extra_info/comid_to_wyt.csv` file, which assigns one of 3 water year types to each year since 1950 for each comid reach. More information on the specifics of that file is contained within the `extra_info/README.md` file. The water year type alteration assessment will group the output metrics by water year type and compare them to the Code for Nature natural functional flow metrics by water year type. This can be more accurate if you have many years of data with a good distribution of different water year types.

## Testing

   To run the test suite found in the `tests/` directory run the following command while in the root directory of this project:

   ``` python
   pytest
   ```

   Note they are currently meaningless as the logic has been getting updated so rapidly. A robust test suite will be made once the major logic changes have ceased to help the maintainability of this repo.

## Known Differences

   Although intended to be a direct upgrade of the reference flow calculator and the UCDavis Flashy flow calculator there are some known differences listed below:

   1. Data filtering:

      The updated calculator requires no more then 18 days of missing data per water year and allows up to 7 days of consecutive missing data. The previous recommendation was to require 358 days of data to run a year. These differences may result in slight changes in metrics that are summarized over multiple years, including peak flow metrics.

   2. New low flow metrics:

      After talking with the original author the low flow metrics have been adapted to fit in with the existing calculator(s) better, most notably this includes: the calculated DS_Tim is used as the start date whenever it is available and June 1st is used otherwise. The end date is always December 31st. For years classified as perennial the number of low flow days is not calculated to draw more attention to the minimum 7 day average metrics and vise versa for years classified as intermittent.

## Questions and Comments

All questions or comment are encouraged to be sent to <nenerson@foundryspatial.com>

### Extra info

There are other README.md files within this project they can be found in the following directories: `extra_info/`, `user_input_files/` and `user_output_files/` directories. There is also a ReadMe.csv file from the reference flow calculator in `extra_info/`. Make sure to check them for a bit more information about the calculator.
