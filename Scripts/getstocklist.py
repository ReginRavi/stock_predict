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
    """Fetch the table column labelled 'Name' across all pages of the screen and return all stocks listed there."""
    session = session or build_session()
    all_names: List[str] = []
    page = 1

    while True:
        sep = "&" if "?" in url else "?"
        page_url = f"{url}{sep}page={page}"
        response = session.get(page_url)
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        target_cols = {"name", "company", "company name"}
        name_header = next(
            (th for th in soup.find_all("th") if th.get_text(strip=True).lower() in target_cols),
            None,
        )
        if not name_header:
            if page == 1:
                raise RuntimeError("Could not find the 'Name' or 'Company' column header in the page.")
            break

        header_row = name_header.find_parent("tr")
        headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
        name_index = -1
        for idx, h in enumerate(headers):
            if h.strip().lower() in target_cols:
                name_index = idx
                break

        if name_index == -1:
            if page == 1:
                raise RuntimeError("Stock name/company column not present in header row.")
            break

        table = name_header.find_parent("table")
        if not table:
            if page == 1:
                raise RuntimeError("Unable to locate the table containing the stock names column.")
            break

        body = table.find("tbody") or table
        page_names: List[str] = []
        for row in body.find_all("tr"):
            if row.find("th"):
                continue
            cells = row.find_all(["td", "th"])
            if len(cells) <= name_index:
                continue
            cell = cells[name_index]
            a_tag = cell.find("a")
            cell_text = a_tag.get_text(strip=True) if a_tag else cell.get_text(strip=True)
            if cell_text and cell_text.lower() not in target_cols:
                page_names.append(cell_text)

        if not page_names:
            break

        all_names.extend(page_names)

        # Check if next page exists
        has_next = False
        pagination = soup.select_one(".pagination, ul.pagination, div.pagination")
        if pagination:
            next_btn = pagination.find(lambda el: "Next" in el.get_text())
            if next_btn:
                has_next = True
        elif f"page={page + 1}" in response.text:
            has_next = True

        if not has_next:
            break

        page += 1

    if not all_names:
        raise RuntimeError("No stock names found under the 'Name' column.")
    return all_names


def save_stock_names(names: List[str], directory: str = "output") -> Path:
    """Persist the names to txt files named after today's date."""
    today_str = date.today().isoformat()
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save YYYY-MM-DD.txt for pipeline compatibility
    date_path = out_dir / f"{today_str}.txt"
    date_path.write_text("\n".join(names) + "\n", encoding="utf-8")
    
    # Save stocklist_YYYY-MM-DD.txt and stocklist.txt
    stocklist_date_path = out_dir / f"stocklist_{today_str}.txt"
    stocklist_date_path.write_text("\n".join(names) + "\n", encoding="utf-8")
    
    stocklist_path = out_dir / "stocklist.txt"
    stocklist_path.write_text("\n".join(names) + "\n", encoding="utf-8")
    
    print(f"💾 Saved stock list to {stocklist_date_path}")
    return date_path


if __name__ == "__main__":
    stocks = fetch_stock_names(URL)
    destination = save_stock_names(stocks)
    print(f"Saved {len(stocks)} stock names to {destination}")
