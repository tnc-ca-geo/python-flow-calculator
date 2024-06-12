Each input file will generate 4-6 output files in a sub directory named after the time of the run:

1. drh
2. annual flow matrix
3. annual flow result
4. supplementary metrics
5. alteration assessment (optional)
6. wyt alteration assessment (optional)

If the output has been told to be batched each file will only individually produce

1. drh

The remainder of the files will then be made into combined files in the output sub-directory. If you want all files to be output in addition to the combined files when batching you can switch the boolean value `DELETE_INDIVIDUAL_FILES_WHEN_BATCH` in constants.py from True to False 
