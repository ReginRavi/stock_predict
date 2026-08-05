import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

#URL = "https://www.screener.in/screens/2375280/bearish-crossovers/"
#URL = "https://www.screener.in/screens/2703064/bearishcrossover2/"
URL ="https://www.screener.in/screens/3804271/below50/"

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session


def fetch_stock_names(url: str, session: Optional[requests.Session] = None) -> List[str]:
    """Fetch the table column labelled 'Name' and return all stocks listed there."""
    session = session or build_session()
    response = session.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    name_header = next(
        (th for th in soup.find_all("th") if th.get_text(strip=True) == "Name"),
        None,
    )
    if not name_header:
        raise RuntimeError("Could not find the 'Name' column header in the page.")

    header_row = name_header.find_parent("tr")
    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
    try:
        name_index = headers.index("Name")
    except ValueError as exc:
        raise RuntimeError("'Name' column not present in header row.") from exc

    table = name_header.find_parent("table")
    if not table:
        raise RuntimeError("Unable to locate the table containing the 'Name' column.")

    body = table.find("tbody") or table
    names: List[str] = []
    for row in body.find_all("tr"):
        if row.find("th"):
            continue
        cells = row.find_all(["td", "th"])
        if len(cells) <= name_index:
            continue
        cell_text = cells[name_index].get_text(strip=True)
        if cell_text:
            names.append(cell_text)

    if not names:
        raise RuntimeError("No stock names found under the 'Name' column.")
    return names


def save_stock_names(names: List[str], directory: str = "output") -> Path:
    """Persist the names to a txt file named after today's date."""
    filename = f"{date.today().isoformat()}.txt"
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / filename
    output_path.write_text("\n".join(names) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    stocks = fetch_stock_names(URL)
    destination = save_stock_names(stocks)
    print(f"Saved {len(stocks)} stock names to {destination}")
