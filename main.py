import pandas as pd
from pathlib import Path
import re

# define the root
BASE_TEMPLATE = Path("base_template/BASE.TRAIN")
SCHEDULE_FILE = Path("data/schedule.xlsx")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# read RTC templex file
with open(BASE_TEMPLATE, "r", encoding="utf-8") as f:
    template_text = f.read()

# read text file
df = pd.read_excel(SCHEDULE_FILE)

# substitute the text file
def generate_train_text(row, base_text):
    '''

    :input row:
            Freight #
            Increment (min)
            Network	Start Day
            Train Symbol
            Scheduled Departure	Comment
    :return:
            BASE.TRAIN
    '''
    text = base_text

    # Train Symbol
    text = re.sub(r"Train symbol:\s*\S+", f"Train symbol: {row['Train Symbol']}", text)

    # Start Day & Start Day
    text = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?(AM|PM)?\b", f"{row['Scheduled Departure']}", text, count=1)

    # Comment (Eastbound Local / Westbound Local)
    text = re.sub(r"Eastbound Local|Westbound Local|Local", f"{row['Comment']}", text)

    return text


for _, row in df.iterrows():
    network = row["Network"]
    symbol = row["Train Symbol"]

    output_path = OUTPUT_DIR / f"{network}" / f"{symbol}"
    output_path.mkdir(parents=True, exist_ok=True)

    # substitute the text file
    new_text = generate_train_text(row, template_text)

    # write into BASE.TRAIN generation
    file_path = output_path / "BASE.TRAIN"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_text)

    print(f"Done! Saved to {file_path}")

print("All BASE.TRAIN files created successfully!")