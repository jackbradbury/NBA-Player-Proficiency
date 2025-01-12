import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def fetch_ppg_leaders():
    url = 'https://www.basketball-reference.com/leaders/pts_per_g_career.html'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("Fetching PPG leaders...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    
    if not table:
        raise Exception("Could not find the stats table")
    
    players = []
    for row in table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 3:  # We need at least rank, player name, and PPG
            try:
                rank = cells[0].text.strip()
                player = cells[1].text.strip()
                ppg = float(cells[2].text.strip())
                players.append({
                    'Rank': rank,
                    'Player': player,
                    'PPG': ppg
                })
            except (ValueError, IndexError) as e:
                continue
    
    return players[:200]  # Return only top 200

def main():
    try:
        # Get the top 200 PPG leaders
        players = fetch_ppg_leaders()
        
        if not players:
            print("Error: No player data was collected!")
            return
            
        # Create DataFrame
        df = pd.DataFrame(players)
        
        # Format the output
        print("\nTop 200 NBA Players by Points Per Game:")
        print(df.to_string(index=False))
        
        # Save to CSV
        output_file = 'top_200_nba_players_ppg.csv'
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
