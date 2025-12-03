#!/usr/bin/env python3
"""
Remove inline `style` attributes from all <div> elements in an HTML file
and save the result to an output file.

Usage:
    python3 remove_div_styles.py input.html output.html

If no arguments provided, defaults are:
    input:  input.html
    output: output.html
"""
import sys
import os

# Try to import BeautifulSoup; if missing, attempt to install it automatically.
try:
    from bs4 import BeautifulSoup
except ImportError:
    # Attempt to install bs4
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

def remove_div_styles(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    for div in soup.find_all("div"):
        if "style" in div.attrs:
            del div.attrs["style"]
    # Return HTML as string without altering other formatting more than necessary
    return str(soup)

def main():
    # Parse command line args
    if len(sys.argv) >= 3:
        in_path = sys.argv[1]
        out_path = sys.argv[2]
    elif len(sys.argv) == 2:
        in_path = sys.argv[1]
        out_path = "output.html"
    else:
        in_path = "input.html"
        out_path = "output.html"

    if not os.path.isfile(in_path):
        # If input file doesn't exist, read from stdin if available
        try:
            stdin_data = sys.stdin.read()
            if not stdin_data:
                raise FileNotFoundError(f"Input file '{in_path}' not found and no data on stdin.")
            html = stdin_data
        except Exception as e:
            raise SystemExit(str(e))
    else:
        with open(in_path, "r", encoding="utf-8") as f:
            html = f.read()

    cleaned = remove_div_styles(html)

    # Write output
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

if __name__ == "__main__":
    main()
