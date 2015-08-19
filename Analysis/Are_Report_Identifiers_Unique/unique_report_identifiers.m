csv_directory = '/Users/Patrick/Google_Drive/School/CMU/Service_Project/Frac/Data/CSVs';
well_info = readtable(strcat(csv_directory,'/well_info.csv'));
%%
report_identifiers = well_info.Report_Identifier;
unique_report_identifiers = unique(report_identifiers);
[num_unique,~] = size(unique_report_identifiers);
[num_report_identifiers,~] = size(report_identifiers);

display(num_report_identifiers);
display(num_unique);
