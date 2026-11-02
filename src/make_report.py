import json
import os
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, PageBreak

with open("data/processed/summary.json", encoding="utf-8") as f:
    S = json.load(f)

st = getSampleStyleSheet()
E = []


def esc(x):
    return escape(str(x))


def pairs(items, unit=""):
    return esc("; ".join(f"{a} ({b}{unit})" for a, b in items))


def triples(items):
    return esc("; ".join(f"{a} (avg {b}, {c} restaurants)" for a, b, c in items))


def h(t):
    E.append(Paragraph(t, st["Heading2"]))


def p(t):
    E.extend([Paragraph(t, st["Normal"]), Spacer(1, 6)])


def img(f, w, hgt):
    path = "figures/" + f
    if os.path.exists(path):
        E.extend([Image(path, width=w, height=hgt), Spacer(1, 10)])


bands = "; ".join(f"{k}: {v}" for k, v in S["rating_by_band"].items())

E.append(Paragraph("Zomato Bangalore Restaurants: Analysis Report", st["Title"]))
p("Dataset: Kaggle <i>bhanupratapbiswas/zomato</i> (Bangalore restaurants). After removing broken "
  f"and duplicate rows there are {S['n_restaurants']} restaurants, of which {S['n_rated']} have a "
  f"rating (mean {S['mean_rating']}). Restaurants marked NEW or without a rating were excluded from "
  "rating analysis and not filled in. Costs are for two people in Indian rupees and were converted "
  "to USD with one approximate rate (<b>WRITE YOUR RATE SOURCE AND DATE HERE</b>). The dataset has no "
  "review text, so the wordclouds use cuisines and the dishes people liked.")
img("overview.png", 440, 147)

h("1. Cuisines vs rating")
p(f"Most common cuisines: {pairs(S['most_common_cuisines'])}. "
  f"Highest rated cuisines (at least 30 restaurants): {pairs(S['top_rated_cuisines'])}.")
img("cuisine.png", 460, 197)
img("wordcloud_cuisines.png", 400, 200)
img("wordcloud_dishes.png", 400, 200)
p(f"Most mentioned liked dishes: {pairs(S['top_dishes'])}.")

E.append(PageBreak())
h("2. Location hotspots")
p(f"Locations with the most restaurants: {pairs(S['top_hotspots'])}. "
  f"Highest rated locations: {triples(S['top_rated_locations'])}.")
img("locations.png", 460, 197)
img("heatmap_loc_type.png", 440, 280)

E.append(PageBreak())
h("3. Price and other factors vs rating")
p(f"Spearman correlation of cost with rating: {S['rho_cost']}; votes with rating: {S['rho_votes']}. "
  f"Average rating by price band: {esc(bands)}. "
  f"Online ordering (no / yes): {S['online_order']['no']} / {S['online_order']['yes']}. "
  f"Table booking (no / yes): {S['book_table']['no']} / {S['book_table']['yes']}. "
  f"Best restaurant types by rating: {triples(S['top_rest_types'])}. "
  "These are associations, not proof of cause.")
img("price_box.png", 380, 217)
img("corr.png", 340, 243)

h("4. Recommendations")
recs = [
    f"<b>Partnerships:</b> start with the busiest locations ({pairs(S['top_hotspots'][:3])}) and the "
    f"best rated ones ({triples(S['top_rated_locations'][:3])}).",
    f"<b>Content ideas:</b> publish 'best of' guides around the most common cuisines "
    f"({pairs(S['most_common_cuisines'][:3])}) and the most liked dishes ({pairs(S['top_dishes'][:3])}).",
    f"<b>Underserved cuisines:</b> highly rated but with few restaurants: {triples(S['gap_cuisines'][:3])}. "
    "Feature and promote these.",
    f"<b>Price positioning:</b> average rating by price band is {esc(bands)}. Highlight the bands "
    "that score best and curate lists per band.",
    f"<b>Features:</b> online ordering ratings (no / yes: {S['online_order']['no']} / {S['online_order']['yes']}) "
    f"and table booking (no / yes: {S['book_table']['no']} / {S['book_table']['yes']}). "
    "Promote a feature only if the difference supports it.",
]
for r in recs:
    p("- " + r)

h("5. Limitations")
p("Single snapshot in time, Bangalore only, no review text, ratings are self-selected and many "
  "restaurants are unrated, results are correlations only, and the exchange rate is approximate.")

SimpleDocTemplate("Zomato_Report.pdf", pagesize=A4).build(E)
print("Saved Zomato_Report.pdf")