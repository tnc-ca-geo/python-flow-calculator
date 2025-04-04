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
5. [Output Data](#output-data)
6. [Testing](#testing)
7. [Known Differences](#known-differences)
8. [Manual Adjustments](#manual-adjustments)
9. [References](#references)
10. [Questions and Comments](#questions-and-comments)
   - [Extra info](#extra-info)

## About

This is a remastered functional flows calculator. A majority of the logic has been left unchanged but lots of new functionality has been added. The repository has been refactored to be more maintainable and the dependencies have all been updated. See references at end for more details on the following sources.
- The original version of the reference functional flows calculator was written by Patterson et al. 2020 (https://www.sciencedirect.com/science/article/abs/pii/S002216942030247X), available here (https://github.com/leogoesger/func-flow).
- The statewide hydrologic stream classification used to adjust parameters was developed by Lane et al. 2018 (https://link.springer.com/article/10.1007/s00267-018-1077-7).
- Information on how to use these metrics and additional references are described in the California Environmental Flows Framework technical report (https://ceff.ucdavis.edu).
- In particular, the alteration assessment is described in an appendix to the technical report by Grantham (https://ceff.ucdavis.edu/sites/g/files/dgvnsk5566/files/media/documents/Appendix_J%20Assessing%20Flow%20Alteration.pdf), and uses modeled unimpaired functional flow metrics developed by Grantham et al. 2022 (https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2022.787473/full). The modeled natural metrics are available at https://rivers.codefornature.org
- This version incorporates the flashy functional flows calculator developed by Carpenter et al. 2025 (https://github.com/camcarpenter6/Alternate-Ruleset-FFC-BETA). This version also incorporates Carpenter et al.'s decision tree for when to use the reference vs flashy calculator.
- This code incorporates new low flow metrics by Ayers et al. 2024 (https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2023WR035768) which have an R implementation (https://github.com/jessayers20/Functional-Low-Flows).
- Additional functionality has been implemented from the ffc api client R package developed by Peek and Santos (https://github.com/ceff-tech/ffc_api_client).

This remastered version was authored by Nathan Emerson of Foundry Spatial, with input from Kirk Klausmeyer and Bronwen Stanford of The Nature Conservancy.

This project was funded by the California Wildlife Conservation Board Stream Flow Enhancement Program under Proposition 1, funding awarded to The Nature Conservancy of California.

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

   There are two main modes of usage for the calculator. Firstly there is the questionnaire, this mode is intended for more casual use. It will ask you a series of questions about the data you are trying to calculate metrics on. Secondly there is the batch processing csv mode. This mode is intended for users who want to process large amounts of data from many data sources and don't want to spend the time entering answers for every data source. More in-depth descriptions of how to use each mode can be found below. Regardless of data type at least one complete water year is required for the data to successfully run

### Data Sources

   Currently there are 3 supported data sources for the functional flows calculator:

   1. [USGS](https://www.usgs.gov/) gage data downloaded using the [dataretrieval-python](https://github.com/DOI-USGS/dataretrieval-python) package developed by USGS. This API is very speedy and seems well supported! Currently the following [parameter ids](https://help.waterdata.usgs.gov/parameter_cd?group_cd=PHY) are supported: 1. 00060 (discharge in cf/s) and 2. 72137 (discharge, tidally filtered, in cf/s). A couple example gage ids are 11274500 and 11522500 if you wish to test it out.
   2. [CDEC](http://cdec.water.ca.gov/) gage data downloaded using the CDEC API. Note that this api is not documented anywhere and is very slow. Currently only parameter ids 20, 41 and 165 (discharge) are supported. Where possible use USGS gage data or take the files downloaded by the flow calculator on the first go through and use them as user uploaded data to save time. Data is downloaded to the /gage_data directory if you wish to view it after the flow calculator runs. A couple example gage ID's are 'NRN' and 'LCH' if you wish to test it out. Note: CDEC full natural flow "gages" are not included in this dataset as they include many negative values and the data cannot be run through the calculator without cleaning.
   3. User uploaded data. If you have a csv of observations or data from a different data source that is not supported it can be accepted. Ensure all CSVs to be uploaded have a column labeled `flow` and a column labeled `date` it is fine if more columns exist but those two must as they are used as the observations of discharge in cf/s at the given date. If you plan on using Questionnaire mode please ensure your formatted csv files are all in `user_input_files/`. An example file is located at `user_input_files/example_input.csv`

### Questionnaire Mode

   In this mode you will be asked a series of questions about each file you want to upload or gage data you want to analyze. It is recommended for poking around or quickly checking things. For large amounts of processing it will be very tedious to use. You will be locked to just one of the three supported data sources when using this mode at a time.

### Batch CSV Mode

   In this mode your input will be read from a specifically formatted csv file. You will be asked a few general questions at the start of the calculator including: if you want an alteration assessment or not.

   After entering this information it will automatically proceed calculating for all the data supplied in the batch csv. This is done so users with an exceptionally large amount of data don't need to wait for all the csvs to download then confirm before the calculations start.

#### Formatting the CSV

   The batch processing csv needs the following column headers (case sensitive) to work: `usgs`, `cdec`, `path`, `comid`, `class`, `lat`, `lng` or `lon`, `calculator`. More columns can exist but those ones are required and any other columns will be ignored by the calculator. Every row in the csv must have data entered in one and only one of the following columns: `usgs`, `cdec` or `path`. This is the minimum data needed for the calculator to fetch the streamflow data needed to run. If you are providing streamflow data in a file, enter the path to the file in the `path` column, and then fill out at least one of the following columns or columns groups: `comid`, `class` or `lat` AND `lng` for the best results. If you decide to leave these columns blank the calculator will still be able to run but it is not recommended as the calculator will use the default flow class which may produce inaccurate results for the supplied data.

   `usgs`: the `usgs` column is expected to be a USGS gage id. Often this is a 10 digit number such as 11023250 (see [the Data Sources section](#data-sources) above for more detail). This information will be used to fetch flow data from the USGS API.

   `cdec`: the `cdec` column is expected to be a CDEC gage id. Often this is a 3 character string such as "SFH" (see [the Data Sources section](#data-sources) above for more detail). This information will be used to fetch flow data from the CDEC API.

   `path`: the `path` column is expected to be a file path to user provided flow data (see [the Data Sources section](#data-sources) above for more information on how). `path` can be a file path to the file relative to the root of this repository or a total path on your machine. This information will be used to fetch flow data from a file on your computer!

   `class`: the `class` column if provided is expected to be the stream classification from one of the following nine options: 'SM', 'HSR', 'LSR', 'WS', 'GW', 'PGR', 'FER', 'RGW', 'HLP'  that matches the classification of your data. More information on the different stream classes can be found at the [*eFlows website*](https://eflows.ucdavis.edu/hydrology) *Note this website has not been available recently*. This information is used to determine what set of parameters to use to calculate metrics on the supplied data. If this column does not have data and cannot be inferred from the below columns the default flow class will be used ("LSR").

   `comid`: the `comid` column if provided is expected to be a COMID sourced from the [NHDPlusV2 dataset](https://www.epa.gov/waterdata/get-nhdplus-national-hydrography-dataset-plus-data) that your selected gage/user uploaded flow data samples from. This column is particularly important when doing alteration assessments as the expected metrics to be compared against are precalculated per-comid in [the natural flows database](https://rivers.codefornature.org/#/home). This information will additionally be used to look up stream class of the supplied data using the file `extra_info/comid_to_stream_class.csv` if the `class` column was not already populated above. Lastly this information is used to find the water year type for each year in the supplied data more information on this in the [Alteration Assessments](#alteration-assessments) section.

   `lat` & `lng`: the `lat` & `lng` columns if provided are expected to be the latitude & longitude pair that represent the point of the gage or where the user uploaded data was obtained in EPSG:4326. This information will be used to "snap" to the closest stream and fetch its comid using [the pyNHD package](https://github.com/hyriver/pynhd). This comid information is then used in place of the `comid` field if its not populated which is then inturn used to populate the `class` field if its not populated. The `lng` column can also be entered as `lon` if that is more convenient. CAUTION: selecting COMID using lat and long is prone to error and is not recommended.

   `calculator`: the `calculator`column if provided must be either "Flashy" or "Reference". Supplying "Flashy" will make that dataset's functional flow metrics be calculated using a translated version of the [UCDavis flashy calculator](https://github.com/camcarpenter6/Alternate-Ruleset-FFC-BETA) whereas "Reference" will make that dataset's functional flow metrics be calculated using an updated version of [the reference functional flows calculator](https://github.com/leogoesger/func-flow). Leaving the field blank will let the program determine which calculator will produce the best results for your data by using the nature of your input data, the flow class and the metrics produced by the Reference calculator. It is recommended to leave this field blank in almost all cases.

   To run, the calculator needs information on the stream class of the data or it will assume the data belongs to the "LSR" class. A few of the methods the calculator can use to get this information has been detailed above (using columns supplied by the user). There are a couple of other methods the calculator can use to populate this data if it is missing and the user is using gage data (supplied by the `usgs` column or the `cdec` column rather then the `path` column). The first option is to use file `extra_info/filtered_stream_gages_v3c_20240311.csv` which contains many gages and their associated comid's to lookup the comid and then use the comid to get the stream class using the `extra_info/comid_to_stream_class.csv` file. If the gage cannot be found within the `extra_info/filtered_stream_gages_v3c_20240311.csv` file then the metadata for the gage will be downloaded or scraped to obtain the latitude and longitude of the gage which will be used as above in the `lat` & `lng` section to obtain the stream class.

   You can see an example batch csv in `batch_example.csv` with some dummy numbers. It covers many of the different cases mentioned above. Feel free to use it and see how the batch processing functionality works before making your own csv.

### Alteration Assessments

   Alteration assessments are one of the core functionalities imported from [the ffc api client](https://github.com/ceff-tech/ffc_api_client), following methods developed by [Grantham](https://ceff.ucdavis.edu/sites/g/files/dgvnsk5566/files/media/documents/Appendix_J%20Assessing%20Flow%20Alteration.pdf). They are done by taking the observed functional flows computed from your data and comparing them with modeled natural functional flow metrics retrieved via [the Natural Flows Database api](https://rivers.codefornature.org/#/data) using your comid as the key. If one or more of your supplied comid's (either auto populated or manually supplied) does not exist in the Natural Flows Database you will get a warning in the command line interface but all of the remaining locations will still have their alteration assessed.

   In addition to a default alteration assessment there is also the possibility to do a alteration assessment by water year type. For this to be possible your comid must be found within the `extra_info/comid_to_wyt.csv` file, which assigns one of 3 water year types to each year since 1950 for each comid reach, based on the [Natural Flows Database monthly predictions](https://rivers.codefornature.org/#/data). More information on the specifics of that file is contained within the `extra_info/README.md` file. The water year type alteration assessment will group the output metrics by water year type and compare them to the Natural Flows Database natural functional flow metrics by water year type. This can be more accurate if the observed (input) dataset has many years of data with a good distribution of different water year types.

## Output data

   Data calculated will be output to a folder within the `user_output_files/` directory with the following naming scheme: `<input_file_name>_YYYY-MM-DD-mm` with the `input_file_name` parameter being the gage id or "Multiple" if there several gages were run simultaneously using the batch functionality. For user uploaded time series data `input_file_name` is simply the name of the provided csv file.

   Within that folder there will be several output files including the following files:

   | File name                                             | Short description                                                                   | Required |
   |-------------------------------------------------------|-------------------------------------------------------------------------------------|----------|
   | `<input_file_name>_annual_flow_matrix.csv`            | Flow matrix created by the calculator from the input data to calculate metrics on.   | Yes      |
   | `<input_file_name>_annual_flow_result.csv`            | All of the metrics calculated based on the flow matrix organized by water year.     | Yes      |
   | `<input_file_name>_alteration_assessment.csv`         | Each metric and whether or not it is believed to be altered based on predicted data.| No       |
   | `<input_file_name>_predicted_observed_percentiles.csv`| Predicted and observed percentiles used for the alteration assessment.              | No       |
   | `<input_file_name>_run_metadata.csv`                  | Metadata and parameters used for the run of the calculator                          | Yes      |

   Files with the required field are always output whereas the non required files will be output or not based on user input. Below is a breakdown of most of the files that may need some extra context.

   The content of the `flow_result` file can be broken down in the following table (adapted version of [the original repositories README.csv](https://github.com/leogoesger/func-flow/blob/master/metrics_info/ReadMe.csv) file). Descriptions of results are included below, with more detailed explanations available in the [eFlows documentation](https://eflows.gitbook.io/project/website_summary). Some additional Low Flow metrics are included in the `flow_result` file and are sourced from the [Functional Low Flows Repository](https://github.com/jessayers20/Functional-Low-Flows). All metrics are calculated on an annual basis (for each water year) except for peak flow magnitude.

   | Name                               | Unit               | Code               | Description                                                                                   |
   |------------------------------------|--------------------|--------------------|-----------------------------------------------------------------------------------------------|
   | Fall pulse magnitude               | cfs                | FA_Mag             | Peak magnitude of fall pulse event (maximum daily peak flow during event)                     |
   | Fall pulse timing                  | water year day     | FA_Tim             | Water year day of fall pulse event peak                                                       |
   | Fall pulse duration                | days               | FA_Dur             | Duration of fall pulse event                                                                  |
   | Wet-season low baseflow            | cfs                | Wet_BFL_Mag_10     | Magnitude of wet-season baseflows (10th percentile of daily flows within that season)         |
   | Wet-season median baseflow         | cfs                | Wet_BFL_Mag_50     | Magnitude of wet-season baseflows (50th percentile of daily flows within that season)         |
   | Wet-season timing                  | water year day     | Wet_Tim            | Start date of wet-season in water year days                                                   |
   | Wet-season duration                | days               | Wet_BFL_Dur        | Wet-season baseflow duration (# of days from start of wet-season to start of spring season)   |
   | 2-year flood magnitude             | cfs                | Peak_2             | 2-year recurrence interval peak flow                                                          |
   | 5-year flood magnitude             | cfs                | Peak_5             | 5-year recurrence interval peak flow                                                          |
   | 10-year flood magnitude            | cfs                | Peak_10            | 10-year recurrence interval peak flow                                                         |
   | 2-year flood duration              | days               | Peak_Dur_2         | Total days at or above 2-year recurrence interval peak flow                                     |
   | 5-year flood duration              | days               | Peak_Dur_5         | Total days at or above 5-year recurrence interval peak flow                                     |
   | 10-year flood duration             | days               | Peak_Dur_10        | Total days at or above 10-year recurrence interval peak flow                                    |
   | 2-year flood frequency             | occurrences        | Peak_Fre_2         | Frequency of 2-year recurrence interval peak flow within a season (number of events)                            |
   | 5-year flood frequency             | occurrences        | Peak_Fre_5         | Frequency of 5-year recurrence interval peak flow within a season (number of events)                            |
   | 10-year flood frequency            | occurrences        | Peak_Fre_10        | Frequency of 10-year recurrence interval peak flow within a season (number of events)                           |
   | Spring recession magnitude         | cfs                | SP_Mag             | Spring recession magnitude (daily flow on start date of spring-flow period)                   |
   | Spring timing                      | water year day     | SP_Tim             | Start date of spring in water year days                                                       |
   | Spring duration                    | days               | SP_Dur             | Spring flow recession duration (# of days from start of spring to start of dry-season period) |
   | Spring rate of change              | percent            | SP_ROC             | Spring flow recession rate (median daily rate of change during recession)                     |
   | Dry-season median baseflow         | cfs                | DS_Mag_50          | 50th percentile of daily flow within dry season                                               |
   | Dry-season high baseflow           | cfs                | DS_Mag_90          | 90th percentile of daily flow within dry season                                               |
   | Dry-season timing                  | water year day     | DS_Tim             | Dry-season baseflow start timing                                                              |
   | Dry-season duration                | days               | DS_Dur_WS          | Dry-season baseflow duration                                                                  |
   | Dry-season first Zero Flow Day     | water year day     | DS_No_Flow_Tim     | Date of first day where flow magnitude is <= 0.1 cfs                                          |
   | Dry-season no-flow duration        | days               | DS_No_Flow_Dur     | Longest number of consecutive days with flow magnitude <= 0.1 cfs                                         |
   | Dry-season 7-day low flow magnitude| cfs                | DS_7d_Low_Mag      | Minimum 7-day rolling average magnitude in the dry season                                     |
   | Dry-season 7-day low flow timing   | water year day     | DS_7d_Low_Tim      | Start date of minimum 7-day period in the dry season                                          |
   | Intermittent Classification        | classification     | Int_Class          | Classification of either Perennial or Intermittent based on average no-flow days per season   |
   | Average annual flow                | cfs                | Avg                | Average annual flow                                                                           |
   | Standard deviation                 | cfs                | Std                | Standard deviation of daily flow                                                              |
   | Coefficient of variation           | unitless           | CV                 | Coefficient of variation (standard deviation divided by average annual flow)                  |

   The `alteration_assessment` file's contents can be broken down as follows:

   | Column Name       | Description                                                                                                  |
   |-------------------|--------------------------------------------------------------------------------------------------------------|
   | WYT               | Water Year Type. Categories include "any", "wet", "dry", and "moderate". Wet years are the wettest third of all complete water years from 1951-present, moderate years are the middle third, and dry years are the driest third. "Any" includes all years.                                   |
   | metric            | Flow metric being evaluated (e.g., DS_Dur_WS, DS_Mag_50, FA_Tim).                                            |
   | alteration_type   | Type of alteration found in the flow metric (e.g., "none_found", "high", "low", "late").                     |
   | status            | Likely status of the metric based on alteration type (e.g., "likely_altered", "likely_unaltered").           |
   | status_code       | Numeric code representing the status: 1 (unaltered) or -1 (altered).                                         |
   | median_in_iqr     | Indicates if the median observed value of the metric is within the interquartile range (True or False).      |
   | years_used        | Number of years used for the analysis.                                                                       |
   | sufficient_data   | Indicates if there was sufficient data available for analysis. 10 or more years are reuqred (True or False). |

   More information on what an alteration assessment is can be found in the [Alteration Assessments section](#alteration-assessments).

   The accompanying predicted and observed percentiles used in the alteration assessment can be found in the `predicted_observed_percentiles` file which can be broken down as follows:

   | Column Name      | Description                                                                                                        |
   |------------------|--------------------------------------------------------------------------------------------------------------------|
   | WYT              | Water Year Type the below percentiles are aggregated over. Categories include "any", "wet", "dry", and "moderate". |
   | metric           | Flow metric being evaluated (e.g., DS_Dur_WS, DS_Mag_50, FA_Tim).                                                  |
   | p10              | 10th percentile value of the observed data for the given metric.                                                   |
   | p25              | 25th percentile value of the observed data for the given metric.                                                   |
   | p50              | 50th percentile value (median) of the observed data for the given metric.                                          |
   | p75              | 75th percentile value of the observed data for the given metric.                                                   |
   | p90              | 90th percentile value of the observed data for the given metric.                                                   |
   | p10_predicted    | Model-predicted natural 10th percentile value for the given metric.                                                        |
   | p25_predicted    | Model-predicted natural 25th percentile value for the given metric.                                                        |
   | p50_predicted    | Model-predicted natural 50th percentile value (median) for the given metric.                                               |
   | p75_predicted    | Model-predicted natural 75th percentile value for the given metric.                                                        |
   | p90_predicted    | Model-predicted natural 90th percentile value for the given metric.                                                        |

   More information on the model used can be found in the [Alteration Assessments section](#alteration-assessments)

## Testing

   To run the test suite found in the `tests/` directory run the following command while in the root directory of this project:

   ``` python
   pytest
   ```

   Note they are currently meaningless as the logic has been getting updated so rapidly. A robust test suite will be made once the major logic changes have ceased to help the maintainability of this repo.

## Known Differences

   Although intended to be a direct upgrade of Patterson et al.'s [reference functional flows calculator](https://github.com/leogoesger/func-flow) and Carpenter et al.'s [flashy functional flows calculator](https://github.com/camcarpenter6/Alternate-Ruleset-FFC-BETA) there are some known differences listed below:

   1. Data filtering:

      The updated calculator allows up to 36 days of missing or NA data and up to 7 days of consecutive missing or NA data per water year. The previous recommendation was to require 358 days of data to run a year. These differences may result in slight changes in metrics that are summarized over multiple years, including peak flow metrics. In particular, since the dry season extends into the subsequent water year, if the subsequent year is missing, dry season magnitude and duration metrics will not calculate.

   2. New low flow metrics:

      This version adds several low flow metrics which were not in the original calculator: DS_No_Flow_Dur, DS_No_Flow_Tim, DS_7d_Low_Mag, and DS_7D_Low_Tim. All of these seek to identify the driest period of the year. After talking with the original author the low flow metrics have been adapted to fit in with the existing calculator(s) better, most notably this includes: the calculated DS_Tim is used as the start of the search window for these metrics whenever it is available and June 1st is used otherwise. The end of the search window is always December 31st. For years classified as perennial the number of low flow days is not calculated to draw more attention to the minimum 7 day average metrics and vise versa for years classified as intermittent.

   3. Water year type and intermittent/perennial classification:

      Water year type is assigned for years after 1950 using the Natural Flows Database: [rivers.codefornature.org](rivers.codefornature.org). Years are divided in equal thirds into wet (0-33.3% exceedance), average (33.4-66.6% exceedance), and dry (66.7-100% exceedance).
      Results for each year of a timeseries and for each timeseries overall are classified as either intermittent or perennial flow. A year was classified as intermittent if there were at least 5 consecutive days of zero flows (<=0.1cfs) during the dry season, and a stream was defined as intermittent if 15% or more of years were classified as intermittent. These are defined according to the methods in Ayers et al. 2024 ([https://onlinelibrary.wiley.com/doi/abs/10.1029/2023WR035768](https://onlinelibrary.wiley.com/doi/abs/10.1029/2023WR035768)).

   4. Corrections to reference flow calculator:

      Several minor errors that had been identified in the original version of the calculator were corrected.
         - Fall timing of 0 is no longer permitted, since this would occur in the previous water year.
         - Spring magnitude for rain fed systems now matches the value at the start day (4 days after the last peak of the wet season).
         - Years that are both divisible by 100 and 4 are no longer considered leap years ie 1900 is not a leap year but was being considered one.

## Manual Adjustments
All calculator parameters can be adjusted manually using the params.py file.

In addition, the following settings can be adjusted in `utils/constants.py`:
- To output individual files in addition to a combined file when running multiple gages switch `DELETE_INDIVIDUAL_FILES_WHEN_BATCH` from `True` to `False`
- To modify the water year start date change `WY_START_DATE` from `'10/1'` to another date in `mm/dd` format
- To produce a Dimensionless Reference Hydrograph in addition to the normal output files change `PRODUCE_DRH` from `False` to `True`

The remainder of the constants in the `constants.py` file are not recommended to be manually changed unless you are very familiar with the inner workings of the calculator.
## References

Ayers, J. R., Yarnell, S. M., Baruch, E., Lusardi, R. A., & Grantham, T. E. 2024. Perennial and non‐perennial streamflow regime shifts across California, USA. Water Resources Research, 60, e2023WR035768. https://doi.org/10.1029/2023WR035768

Baker, D. B., R. P. Richards, T. T. Loftus, and J. W. Kramer. 2004. A New Flashiness Index: Characteristics and Applications to Midwestern Rivers and Streams. JAWRA Journal of the American Water Resources Association 40:503–522. https://doi.org/10.1111/j.1752-1688.2004.tb01046.x

California Environmental Flows Working Group (CEFWG). 2021. California Environmental Flows Framework Version 1.0. California Water Quality Monitoring Council Technical Report 65 pp. https://ceff.ucdavis.edu/tech-report.

Grantham, T. E., D. M. Carlisle, J. Howard, B. Lane, R. Lusardi, A. Obester, S. Sandoval-Solis, B. Stanford, E. D. Stein, K. T. Taniguchi-Quan, S. M. Yarnell, and J. K. H. Zimmerman. 2022. Modeling Functional Flows in California’s Rivers. Frontiers in Environmental Science 10. https://doi.org/10.3389/fenvs.2022.787473

Lane, B.A., S. Sandoval-Solis, E.D. Stein, S.M. Yarnell, G.B. Pasternack, and H.E. Dahlke. 2018. Beyond metrics? The role of hydrologic baseline archetypes in environmental water management. Environmental Management 62:678-693. https://doi.org/10.1007/s00267-018-1077-7

Patterson, N. K., B. A. Lane, S. Sandoval-Solis, G. B. Pasternack, S. M. Yarnell, and Y. Qiu. 2020. A hydrologic feature detection algorithm to quantify seasonal components of flow regimes. Journal of Hydrology 585:124787. https://doi.org/10.1016/j.jhydrol.2020.124787

Santos, N., & Peek, R. (2020). FFC API Client (Version 0.9.8.3) [Computer software]. https://github.com/ceff-tech/ffc_api_client

Yarnell, S. M., G. E. Petts, J. C. Schmidt, A. A. Whipple, E. E. Beller, C. N. Dahm, P. Goodwin, and J. H. Viers. 2015. Functional Flows in Modified Riverscapes: Hydrographs, Habitats and Opportunities. BioScience 65:963–972. https://doi.org/10.1093/biosci/biv102

Yarnell, S. M., E. D. Stein, J. A. Webb, T. Grantham, R. A. Lusardi, J. Zimmerman, R. A. Peek, B. A. Lane, J. Howard, and S. Sandoval-Solis. 2020. A functional flows approach to selecting ecologically relevant flow metrics for environmental flow applications. River Research and Applications 36:318–324. https://doi.org/10.1002/rra.3575


## Questions and Comments

All questions or comment are encouraged to be sent to <kklausmeyer@tnc.org> or <bronwen.stanford@tnc.org>

### Extra info

There are other README.md files within this project they can be found in the following directories: `extra_info/` and `user_input_files/`. Make sure to check them for a bit more information about the calculator.

