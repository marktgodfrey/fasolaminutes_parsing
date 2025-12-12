from bs4 import BeautifulSoup
import json
import re

# INPUT_HTML = "SongData_Denson_1991.html"
# OUTPUT_JSON = "SongData_1991.json"
INPUT_HTML = "SongData_Denson_2025.html"
OUTPUT_JSON = "SongData_2025.json"

def strip_parenthetical(meter_text):
    if not meter_text:
        return meter_text
    # remove the final " ( ... )" including parentheses
    return re.sub(r"\s*\([^)]*\)$", "", meter_text).strip()

# ---- parse ----
with open(INPUT_HTML, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

entries = []

for div in soup.select("div.entry"):
    # page number like "28t", "35", etc.
    num_span = div.find("span", class_="num")
    if not num_span:
        continue
    pagenum = num_span.get_text(strip=True)

    # title like "Aylesbury"
    title_span = div.find("span", class_="title")
    title = title_span.get_text(strip=True) if title_span else None

    # poet ("Words" row)
    poet = None
    words_td = div.select_one("tr.words td")
    if words_td:
        # get all text inside, including years, but strip whitespace
        poet = words_td.get_text(separator=" ", strip=True)
        poet = re.sub(r'\s+,', ',', poet)
        poet = re.sub(r',\s+', ', ', poet)

    # composer ("Music" row)
    composer = None
    music_td = div.select_one("tr.music td")
    if music_td:
        composer = music_td.get_text(separator=" ", strip=True)
        composer = re.sub(r'\s+,', ',', composer)
        composer = re.sub(r',\s+', ', ', composer)

    # meter ("Meter" row)
    meter = None
    meter_td = div.select_one("tr.meter td")
    if meter_td:
        meter_raw = meter_td.get_text(strip=True)
        meter = strip_parenthetical(meter_raw)

    # full song text (with stanza breaks)
    text_p = div.find("p", class_="text")
    song_text = None
    if text_p:
        # turn <br> into newlines
        raw = text_p.get_text("\n")

        # split and clean line endings
        lines = [line.rstrip() for line in raw.splitlines()]

        # strip leading/trailing blank lines
        while lines and lines[0] == "":
            lines.pop(0)
        while lines and lines[-1] == "":
            lines.pop()

        # collapse runs of blank lines to a single blank line
        norm_lines = []
        last_blank = False
        for line in lines:
            if line == "":
                if not last_blank:
                    norm_lines.append(line)
                last_blank = True
            else:
                norm_lines.append(line)
                last_blank = False

        song_text = "\n".join(norm_lines)

    entries.append(
        {
            "pagenum": pagenum,
            "title": title,
            "poet": poet,
            "composer": composer,
            "meter": meter,
            "text": song_text,
        }
    )

# ---- write JSON ----
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(entries, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(entries)} entries to {OUTPUT_JSON}")
