csv_directory = '/Users/Patrick/Google_Drive/School/CMU/Service_Project/Frac/Data/CSVs';
well_info = readtable(strcat(csv_directory,'/well_info.csv'));

%%
api = well_info.API_Number;
[num_api,~] = size(api);
[unique_api,~,count] = unique(api);
[unique_api_count,~] = size(unique_api);
display(unique_api_count);

%%
unique_counts = accumarray(count,1,[], @sum);
num_repetitions = 1:1:4;

api_repeats = [sum(unique_counts == 2),...
               sum(unique_counts == 3),...
               sum(unique_counts == 4),...
               sum(unique_counts ==5)];
percent_unique = round(unique_api_count/num_api*100);

fig = figure;
    hold on;
    set(findall(gcf,'-property','FontSize'),'FontSize',16);
    title('Count of API numbers vs Number of repetitions');
    xlabel('Number of repetitions');
    set(gca,'Xtick',0:1:4)
    ylabel('Count of API numbers');
    text(2.5,800,sprintf('Unique API numbers:\t%d/%d = %d%%',...
                        unique_api_count,num_api,percent_unique));
    bar(num_repetitions,api_repeats);
    axis tight;
    saveas(gcf,'api_repetitions.png');
    
%%

repeat_api = unique_api(unique_counts > 1);