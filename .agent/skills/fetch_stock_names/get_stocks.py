import requests
from bs4 import BeautifulSoup
import json
import sys
import os
from datetime import date
import argparse

URL = "https://www.screener.in/screens/2703064/bearishcrossover2/?utm_source=email&utm_medium=alerts&utm_campaign=screen-results"

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session

def fetch_stock_names(url: str):
    session = build_session()
    try:
        response = session.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    name_header = next(
        (th for th in soup.find_all("th") if th.get_text(strip=True) == "Name"),
        None,
    )
    if not name_header:
        return []

    header_row = name_header.find_parent("tr")
    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
    try:
        name_index = headers.index("Name")
    except ValueError:
        return []

    table = name_header.find_parent("table")
    if not table:
        return []

    body = table.find("tbody") or table
    names = []
    for row in body.find_all("tr"):
        if row.find("th"):
            continue
        cells = row.find_all(["td", "th"])
        if len(cells) <= name_index:
            continue
        cell_text = cells[name_index].get_text(strip=True)
        if cell_text:
            names.append(cell_text)

    return names

def save_to_file(names: list, base_dir: str):
    output_dir = os.path.join(base_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{date.today().isoformat()}.txt"
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(names) + "\n")
    return file_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch stock names from Screener.in")
    parser.add_argument("--save", action="store_true", help="Save the output to a date-named file in the 'output' directory")
    args = parser.parse_args()

    stocks = fetch_stock_names(URL)
    
    if args.save:
        # Assuming the base directory is the parent of the script's directory for the skill
        # or just the current workspace. Let's use the current working directory.
        saved_path = save_to_file(stocks, os.getcwd())
        print(json.dumps({"stocks": stocks, "saved_to": saved_path}, indent=2))
    else:
        print(json.dumps(stocks, indent=2))
