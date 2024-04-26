# /extra_info

This directory contains several csv's that are used by the functional flows calculator or provide more information for the user.

1. comid_to_wyt.csv:
        This csv contains a highly compressed data structure to reduce the size of the file. The first column
        is the water year type and the second column is the compressed information. The information has been 
        compressed such that it is a 73 digit integer with each digit representing the water year type from 
        1951 to 2023 inclusive for that comid. The mappings are as follows: 0 -> moderate, 1 -> wet, 2 -> dry.
        This table should be updated once a year by appending the correct integer code for each comid's
    
2. Day_of_year_converisons.csv:
        This csv contains conversions between julian dates, water year dates (assuming oct 1st start) and
        calendar dates for both leap years and non leap years
    
3. filtered_stream_gages_v3c_20240311.csv:
        Contains a cut down version of the data set found [here](https://gispublic.waterboards.ca.gov/portal/home/item.html?id=a1aaba4d6cff44dea5dca8e3d4fd0238#overview) to lookup comid from gage id's for both usgs and CDEC
        
4. ReadMe.csv:
        A read me from the original functional flows calculator that contains additional metadata about the calculator, output info metric info and more!

5. comid_to_stream_class.csv:
        A simple lookup table to convert from comid to flow class. Originally sourced from [this file in the ffc_api_client repository](https://github.com/ceff-tech/ffc_api_client/blob/release/ffcAPIClient/data/stream_class_data.rda).