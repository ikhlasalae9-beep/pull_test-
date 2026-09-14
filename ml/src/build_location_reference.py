"""Generate location choices from the final notebook's repaired neighborhood column."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/processed/maisondelux_model_ready_v1.csv'

def build_reference():
    frame = pd.read_csv(SOURCE)
    # Matches notebook cells 19–20: repaired neighborhood, then strip only.
    frame['city'] = frame.city.astype('string').str.strip()
    frame['neighborhood'] = frame.neighborhood_clean.astype('string').str.strip()
    return {city: sorted(set(part.neighborhood.dropna()) - {''})
            for city, part in frame.groupby('city', sort=True)}

if __name__ == '__main__':
    output = ROOT / 'models/neighborhoods_v1.json'
    output.write_text(json.dumps(build_reference(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Generated {output.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}')
