import requests
from bs4 import BeautifulSoup
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import time

def transform_name(name):
    # Handle special characters and remove asterisk for Hall of Fame players
    name = name.replace('*', '').strip()
    # Handle special characters in names
    name = name.replace('Ä', 'c').replace('Å', 'n').replace('Ä£', 'g')
    
    try:
        parts = name.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]  # Take the last part as the last name
            formatted_name = f"{last[0].lower()}/{last[:5].lower()}{first[:2].lower()}"
            return formatted_name
        else:
            print(f"Could not parse name: {name}")
            return None
    except Exception as e:
        print(f"Error processing name {name}: {e}")
        return None

# Read the top 200 players from CSV
try:
    top_200_df = pd.read_csv('top_200_nba_players_ppg.csv')
    names = top_200_df['Player'].tolist()
except Exception as e:
    print(f"Error reading CSV file: {e}")
    names = []

stats = ["Name", "PPG", "APG", 'RPG', 'SPG', 'BPG', 'TPG', 'FG%', 'WS/48', 'BPM', "JBR"]
weights = [4, 5.882352941, 3, 5.555555556, 5.555555556, -5, 80, 350, 9.090909091]
df = pd.DataFrame(columns=stats)

print(f"Processing {len(names)} players...")

for i, name in enumerate(names):
    try:
        current = transform_name(name)
        if not current:
            print(f"Skipping {name} - could not transform name")
            continue
            
        print(f"Processing {i+1}/200: {name}")
        url = f"https://www.basketball-reference.com/players/{current}01.html"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            time.sleep(3)  # Be nice to the server
        except Exception as e:
            print(f"Failed to retrieve data for {name}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        row = [name]
        tables = ["per_game_stats", "per_game_stats", "per_game_stats", "per_game_stats", 
                 "per_game_stats", "per_game_stats", "per_game_stats", "advanced", "advanced"]
        data_points = ['pts_per_g', 'ast_per_g', 'trb_per_g', 'stl_per_g', 'blk_per_g', 
                      'tov_per_g', 'fg_pct', 'ws_per_48', 'bpm']

        for x in range(len(tables)):
            table = soup.find('table', {'id': tables[x]})
            if table:
                footer_section = table.find('tfoot')
                if footer_section:
                    target_row = footer_section.find('tr')
                    if target_row:
                        specific_td = target_row.find('td', {'data-stat': data_points[x]})
                        if specific_td and specific_td.text.strip():
                            try:
                                row.append(float(specific_td.text))
                            except ValueError:
                                print(f"Could not convert {specific_td.text} to float for {name}")
                                row.append(0)
                        else:
                            row.append(0)
                    else:
                        row.append(0)
                else:
                    row.append(0)
            else:
                row.append(0)

        # Calculate the JBR value using weights
        jbr = 0
        for j in range(len(weights)):
            jbr += row[j+1] * weights[j]
        row.append(jbr)

        df.loc[len(df)] = row
        
        if (i + 1) % 10 == 0:
            print(f"Completed {i+1} players")
            
    except Exception as e:
        print(f"Error processing player {name}: {e}")
        continue

# Sort by JBR
df = df.sort_values('JBR', ascending=False).reset_index(drop=True)

# Create spreadsheet
wb = Workbook()
ws = wb.active
ws.title = "Top_200_NBA_Players_JBR"

# Put data into worksheet
for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
    for c_idx, value in enumerate(row, 1):
        ws.cell(row=r_idx, column=c_idx, value=value)

# Save the file
output_file = "Top_200_NBA_Players_JBR.xlsx"
wb.save(output_file)
print(f"\nResults saved to {output_file}")

# Display top 10 players by JBR
print("\nTop 10 Players by JBR:")
print(df[['Name', 'JBR']].head(10).to_string())