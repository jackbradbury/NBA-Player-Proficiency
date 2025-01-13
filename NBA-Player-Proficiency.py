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
    # Handle apostrophes and special cases
    name = name.replace("'", "").replace(".", "")
    
    try:
        parts = name.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]  # Take the last part as the last name
            
            # Convert to lowercase first to handle any case inconsistencies
            last = last.lower()
            first = first.lower()
            
            # Remove any remaining special characters
            last = ''.join(c for c in last if c.isalnum())
            first = ''.join(c for c in first if c.isalnum())
            
            formatted_name = f"{last[0]}/{last[:5]}{first[:2]}"
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

# Special cases for player URL suffixes
player_suffixes = {
    'Kevin Johnson': '02',
    'Walter Davis': '03',
    'Antoine Walker': '02',
    'Anthony Davis': '02',
    'Kemba Walker': '02',
    'Jaylen Brown': '02',
    'Ray Allen': '02'
}

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
        
        # Use special suffix if player is in the dictionary, otherwise use '01'
        suffix = player_suffixes.get(name, '01')
        url = f"https://www.basketball-reference.com/players/{current}{suffix}.html"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            time.sleep(2)  # Be nice to the server
        except Exception as e:
            print(f"Failed to retrieve data for {name}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        row = [name]
        
        # Find all tables and print their IDs for debugging
        all_tables = soup.find_all('table')
        print(f"\nFound {len(all_tables)} tables for {name}")
        for table in all_tables:
            print(f"Table ID: {table.get('id', 'No ID')}")
        
        # Define table IDs and stats to look for
        per_game_table = soup.find('table', {'id': 'per_game_stats'})
        if per_game_table:
            print(f"Found per_game_stats table for {name}")
        else:
            print(f"Could not find per_game_stats table for {name}")
            
        advanced_table = soup.find('table', {'id': 'advanced'})
        
        # Stats to collect from per_game table
        per_game_stats = ['pts_per_g', 'ast_per_g', 'trb_per_g', 'stl_per_g', 'blk_per_g', 
                         'tov_per_g', 'fg_pct']
        # Stats to collect from advanced table
        advanced_stats = ['ws_per_48', 'bpm']
        
        # Function to extract stat from table
        def extract_stat(table, stat_name):
            if not table:
                print(f"Table not found for {name} when looking for {stat_name}")
                return 0
            
            # Print table structure for debugging
            print(f"\nLooking for {stat_name} in table for {name}")
            
            # Try footer first (career stats)
            footer = table.find('tfoot')
            if footer:
                print("Found footer")
                stat_cell = footer.find('td', {'data-stat': stat_name})
                if stat_cell:
                    print(f"Found stat cell in footer with text: {stat_cell.text.strip()}")
                    if stat_cell.text.strip():
                        try:
                            return float(stat_cell.text.strip())
                        except ValueError:
                            print(f"Could not convert footer stat {stat_name} for {name}")
                            pass
                else:
                    print(f"No stat cell found in footer for {stat_name}")
            else:
                print("No footer found")
            
            # If no footer stats, try the last row of the body
            body = table.find('tbody')
            if body:
                print("Found table body")
                rows = body.find_all('tr')
                print(f"Found {len(rows)} rows in body")
                if rows:
                    last_row = rows[-1]
                    stat_cell = last_row.find('td', {'data-stat': stat_name})
                    if stat_cell:
                        print(f"Found stat cell in body with text: {stat_cell.text.strip()}")
                        if stat_cell.text.strip():
                            try:
                                return float(stat_cell.text.strip())
                            except ValueError:
                                print(f"Could not convert body stat {stat_name} for {name}")
                                pass
                    else:
                        print(f"No stat cell found in body for {stat_name}")
            else:
                print("No table body found")
            
            print(f"No valid stat found for {stat_name} for {name}")
            return 0
        
        # Extract per_game stats
        print(f"\nProcessing per_game stats for {name}")
        for stat in per_game_stats:
            value = extract_stat(per_game_table, stat)
            print(f"{name} - {stat}: {value}")
            row.append(value)
        
        # Extract advanced stats
        print(f"\nProcessing advanced stats for {name}")
        for stat in advanced_stats:
            value = extract_stat(advanced_table, stat)
            print(f"{name} - {stat}: {value}")
            row.append(value)

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