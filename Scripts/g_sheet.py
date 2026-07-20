from datetime import date
from pathlib import Path
from urllib.parse import urlparse

URL = "https://www.screener.in/screens/2703064/bearishcrossover2/"


def extract_name(url: str) -> str:
    """Return the last non-empty segment of the URL path."""
    path = urlparse(url).path.strip("/")
    if not path:
        raise ValueError("URL path is empty; nothing to extract.")
    return path.split("/")[-1]


def save_to_file(text: str, directory: str = ".") -> Path:
    """Save text to a file named with today's date (YYYY-MM-DD)."""
    filename = f"{date.today().isoformat()}.txt"
    output_path = Path(directory) / filename
    output_path.write_text(f"{text}\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    extracted_name = extract_name(URL)
    result_path = save_to_file(extracted_name)
    print(f"Saved '{extracted_name}' to {result_path}")
