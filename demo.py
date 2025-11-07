import pandas as pd
from pathlib import Path
import re
from datetime import datetime


TEMPLATE_DIR = Path("base_template")
INPUT_DIR = Path("data")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADING_TEMPLATE = TEMPLATE_DIR / "BASE_Heading.TRAIN"
EB_TEMPLATE = TEMPLATE_DIR / "BASE_EB.TRAIN"
WB_TEMPLATE = TEMPLATE_DIR / "BASE_WB.TRAIN"

heading_text = HEADING_TEMPLATE.read_text(encoding="utf-8")
eb_text = EB_TEMPLATE.read_text(encoding="utf-8")
wb_text = WB_TEMPLATE.read_text(encoding="utf-8")


def format_departure(start_day, sched_time):
    """
    Format the departure time:
        - If Start Day = 0: output format 'HH:MM:SS'
        - If Start Day > 0: output format 'DD:HH:MM:SS'
    """
    # Handle datetime or timestamp directly
    if isinstance(sched_time, (datetime, pd.Timestamp)):
        hh, mm = sched_time.hour, sched_time.minute

    else:
        sched_time = str(sched_time).strip()
        if " " in sched_time and sched_time.count(":") == 2:
            try:
                t = pd.to_datetime(sched_time)
                hh, mm = t.hour, t.minute
            except Exception:
                pass
        else:
            try:
                if "AM" in sched_time.upper() or "PM" in sched_time.upper():
                    t = datetime.strptime(sched_time, "%I:%M %p")
                    hh, mm = t.hour, t.minute
                else:
                    parts = sched_time.split(":")
                    hh = int(parts[0])
                    mm = int(parts[1]) if len(parts) > 1 else 0
            except Exception:
                raise ValueError(f"Invalid time format: {sched_time}")

    time_str = f"{hh:02d}:{mm:02d}:00"
    if start_day > 0:
        time_str = f"{start_day:02d}:{time_str}"
        if start_day >= 1:
            if time_str.startswith("   "):
                time_str = time_str[3:]
            else:
                time_str = time_str.lstrip()

    return time_str


def build_train_block(row, template):
    """
    Replacements:
        - Train symbol
        - Comment (direction)
        - Scheduled Departure
    """
    text = template
    text = re.sub(r"Train symbol:\s*\S+", f"Train symbol: {row['Train Symbol']}", text)
    text = re.sub(r"Eastbound Local|Westbound Local|Local", f"{row['Comment']}", text)

    # departure time replacement
    dep_time = format_departure(int(row['Start Day']), str(row['Scheduled Departure']))

    print(f"\n=== Train {row['Train Symbol']} ===")
    print(f"Target departure time: {dep_time}")
    pattern = re.compile(
        r'(Arrival\s+Departure\s+Dwell Time[^\n]*\n[^\n]*\n\s*-+[^\n]*\n\s+\S+\s+)(\d{1,2}:\d{2}:\d{2}N?|FLOAT)(\s+)(\d{1,2}:\d{2}:\d{2}N?|FLOAT)',
        flags=re.IGNORECASE
    )

    match = pattern.search(text)
    if match:
        print(f"Pattern matched!")
        print(f"Column 2 (Arrival): '{match.group(2)}'")
        print(f"Column 3 (Departure, template): '{match.group(4)}'")
        print(f"Replacing Departure with schedule row: '{dep_time}'")
        text = pattern.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + dep_time, text, count=1)
    else:
        print(f"Pattern did not match")

    return text


for input_file in INPUT_DIR.glob("*.xlsx"):
    print(f"Processing {input_file.name} ...")
    df = pd.read_excel(input_file, engine="openpyxl")

    for network, group_df in df.groupby("Network"):
        print(f"Generating {network}.TRAIN ...")

        merged_text = heading_text + "\n\n"

        for _, row in group_df.iterrows():
            if "Eastbound" in row["Comment"]:
                base_template = eb_text
            elif "Westbound" in row["Comment"]:
                base_template = wb_text
            else:
                raise ValueError(f"Unknown direction: {row['Comment']}")

            block = build_train_block(row, base_template)
            merged_text += block + "\n\n"

        output_path = OUTPUT_DIR / f"{network}.TRAIN"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(merged_text)
        print(f"Generated {output_path} ({len(group_df)} trains)")

print("\nDone! All TRAIN files generated successfully.")