import requests
from bs4 import BeautifulSoup
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def transform_name(name): #turns name into format for url
    first, last = name.split()
    formatted_name = f"{last[0].lower()}/{last[:5].lower()}{first[:2].lower()}"
    
    return formatted_name

names = ["Killian Hayes"]
stats = ["Name", "PPG",	"APG", 'RPG','SPG','BPG','TPG','FG%','WS/48','BPM',"JBR"] #stats that I'm tracking
weights = [4, 5.882352941, 3, 5.555555556, 5.555555556, -5, 80, 350, 9.090909091] #The weight that cooresponds to each
df = pd.DataFrame(columns = stats)


for i in range(len(names)):
    current = transform_name(names[i])
    print(current)
    url = f"https://www.basketball-reference.com/players/" +current+ "01.html" 
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data for " +names[i])
        continue  # Skips player if the request fails
    
    soup = BeautifulSoup(response.text, 'html.parser')
    row = [names[i]] 
    tables = ["per_game_stats", "per_game_stats", "per_game_stats", "per_game_stats", "per_game_stats", "per_game_stats", "per_game_stats", "advanced", "advanced"]
    data_points = [ 'pts_per_g', 'ast_per_g', 'trb_per_g', 'stl_per_g', 'blk_per_g', 'tov_per_g', 'fg_pct', 'ws_per_48', 'bpm']

    
    for x in range(len(tables)):
        table = soup.find('table', {'id': tables[x]})

        if table:
            # Find the footer within the table
            footer_section = table.find('tfoot')
            
            if footer_section:
                # Get the first <tr> in the footer section
                target_row = footer_section.find('tr')
                
                if target_row:
                    # Find the specific <td> with data-stat="exampleDataStat" within this row
                    specific_td = target_row.find('td', {'data-stat': data_points[x]})
                    
                    if specific_td:
                        row.append(float(specific_td.text))
                    else:
                        print("The specific <td> with data-stat='exampleDataStat' was not found in the target row.")
                else:
                    print("No <tr> found in the footer section.")
            else:
                print("Footer section <tfoot> not found in the table.")
        else:
            print("Table with id='exampleTableId' not found.")

    # Calculate the JBR value using weights
    jbr = 0
    for j in range(len(weights)):
        jbr += row[j+1] * weights[j] 
    row.append(jbr)  

    df.loc[i] = row


#create spreadsheet
wb = Workbook()
ws = wb.active
ws.title = input("File Name: ")

#put data into worksheet
for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
    for c_idx, value in enumerate(row, 1):
        ws.cell(row=r_idx, column=c_idx, value=value)

wb.save(ws.title+'.xlsx')