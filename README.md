# Zomato Dataset Analysis

Analysis of restaurant ratings, cuisines, locations and price using Zomato data.

**Dataset:** https://www.kaggle.com/datasets/bhanupratapbiswas/zomato (Bangalore restaurants)

## Contents
- `Zomato_Analysis.ipynb` - cleaning, exploration and visualisations
- `src/` - cleaning, analysis and report scripts
- `Zomato_Report.pdf` - findings and 5 recommendations
- `data/processed/zomato_cleaned.csv` - cleaned data
- `figures/` - charts

## Key findings
- (write 3 or 4 findings from your results here)

## How to run
1. Create a virtual environment and install: `pip install -r requirements.txt`
2. Download `zomato.csv` from Kaggle and put it in `data/raw/`
3. Run:
   - `python src/clean.py`
   - `python src/analyze.py`
   - `python src/make_report.py`

## Notes
Costs are in INR, converted to USD with one approximate rate. The dataset has no review text, so the wordclouds use cuisines and liked dishes..