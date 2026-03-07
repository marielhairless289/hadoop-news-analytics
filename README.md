# HW2 - News Category Dataset Analysis

## Project Log

This file documents every step taken in this project, including all commands and observations.

---

## Step 1: Dataset Download

**Source:** Kaggle — [News Category Dataset](https://www.kaggle.com/datasets/rmisra/news-category-dataset)

**File downloaded:** `News_Category_Dataset_v3.json`

- The dataset is from HuffPost and contains news articles.
- Each line in the file is a JSON object (newline-delimited JSON / NDJSON format).
- Fields in each record:
  - `link` — URL to the article
  - `headline` — Article headline
  - `category` — News category (e.g., U.S. NEWS, COMEDY, POLITICS, etc.)
  - `short_description` — Brief summary of the article
  - `authors` — Author name(s)
  - `date` — Publication date (format: YYYY-MM-DD)

---

## Step 2: Trim the Dataset

To avoid working with the full dataset, the first 5000 lines were extracted into a smaller file.

**Command:**
```bash
head -n 5000 News_Category_Dataset_v3.json > news_headlines.txt
```

**Result:** Created `news_headlines.txt` containing the first 5000 records from the original dataset.

---

## Step 3: Verify the Trimmed File

Checked the first 3 lines of the trimmed file to confirm correct format and content.

**Command:**
```bash
head -n 3 news_headlines.txt
```

**Output (sample records):**
```json
{"link": "https://www.huffpost.com/entry/covid-boosters-uptake-us_n_632d719ee4b087fae6feaac9", "headline": "Over 4 Million Americans Roll Up Sleeves For Omicron-Targeted COVID Boosters", "category": "U.S. NEWS", "short_description": "Health experts said it is too early to predict whether demand would match up with the 171 million doses of the new boosters the U.S. ordered for the fall.", "authors": "Carla K. Johnson, AP", "date": "2022-09-23"}
{"link": "https://www.huffpost.com/entry/american-airlines-passenger-banned-flight-attendant-punch-justice-department_n_632e25d3e4b0e247890329fe", "headline": "American Airlines Flyer Charged, Banned For Life After Punching Flight Attendant On Video", "category": "U.S. NEWS", "short_description": "He was subdued by passengers and crew when he fled to the back of the aircraft after the confrontation, according to the U.S. attorney's office in Los Angeles.", "authors": "Mary Papenfuss", "date": "2022-09-23"}
{"link": "https://www.huffpost.com/entry/funniest-tweets-cats-dogs-september-17-23_n_632de332e4b0695c1d81dc02", "headline": "23 Of The Funniest Tweets About Cats And Dogs This Week (Sept. 17-23)", "category": "COMEDY", "short_description": "\"Until you have a dog you don't understand what could be eaten.\"", "authors": "Elyse Wanshel", "date": "2022-09-23"}
```

**Observation:** Format confirmed correct — each line is a valid JSON object with all expected fields present. Records are from September 2022.

---
