import pandas as pd
from pathlib import Path
import re
from datetime import datetime


BASE_TEMPLATE = Path("base_template/BASE.TRAIN")
INPUT_DIR = Path("data")      # schedule.xlsx
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def extract_first_train_block(template_path: Path) -> str:
    """abstract the first block of Train symbol"""
    text = template_path.read_text(encoding="utf-8")

    pattern = re.compile(r"(=+\n.*?Train symbol:.*?)(?=\n=+|$)", re.DOTALL | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        raise ValueError("No such a Train symbol block on template.")
    return match.group(1)


def format_departure(start_day, sched_time):
    """
        If the start day is 0 in the Excel file, the time can be inputted as HH:MM:SS
        If the start day is 1, it will be 01:HH:MM:SS
    """
    if isinstance(sched_time, (datetime, pd.Timestamp)):
        hh = sched_time.hour
        mm = sched_time.minute
    else:
        sched_time = str(sched_time).strip()
        try:
            if "AM" in sched_time.upper() or "PM" in sched_time.upper():
                t = datetime.strptime(sched_time, "%I:%M %p")
                hh, mm = t.hour, t.minute
            else:
                parts = sched_time.split(":")
                hh = int(parts[0])
                mm = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            raise ValueError(f" Scheduled Departure: {sched_time}")

    time_str = f"{hh:02d}:{mm:02d}:00"
    if start_day > 0:
        time_str = f"{start_day:02d}:{time_str}"
    return time_str


def build_train_block(row, template):
    """
    Search the row from schedule.xlsx
    Substitute the block:
                Train Symbol
                Comment
                Scheduled Departure
    Return:
                The new block!
    """
    text = template
    text = re.sub(r"Train symbol:\s*\S+", f"Train symbol: {row['Train Symbol']}", text)
    text = re.sub(r"Eastbound Local|Westbound Local|Local", f"{row['Comment']}", text)
    dep_time = format_departure(int(row['Start Day']), str(row['Scheduled Departure']))
    text = re.sub(r"\b\d{1,2}:\d{2}:\d{2}N?\b", dep_time, text)
    return text

train_template = extract_first_train_block(BASE_TEMPLATE)

for input_file in INPUT_DIR.glob("*.xlsx"):
    print(f"\nProcessing {input_file.name} ...")
    df = pd.read_excel(input_file, engine="openpyxl")

    # group by Network
    for network, group_df in df.groupby("Network"):
        all_trains_text = ""
        for _, row in group_df.iterrows():
            block = build_train_block(row, train_template)
            all_trains_text += block + "\n\n"
        # output
        output_path = OUTPUT_DIR / f"{network}.TRAIN"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(all_trains_text)
        print(f"Generated {output_path} ({len(group_df)} trains)")

print("\nDone! All TRAIN files generated successfully.")