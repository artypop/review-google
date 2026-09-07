
Stratified panel of Google Maps locations for measuring Google review deletions over 7 crawl waves in 14 days.

**## Headline**

- ***9,048 locations**** total (all distinct Google place_ids)
- ***4,359**** distinct brands / groups
- ***38**** balanced cells (7 industries x 2 regions x 3 size buckets, minus 4 starved travel cells)
- ***~4.81M**** reviews across the panel

**## By region x bucket**

| Region | Mono (1 loc) | Small (4-10) | Large (20-50) | Total |

| --- | --- | --- | --- | --- |

| US | 1,668 | 1,428 | 1,428 | 4,524 |

| EU | 1,668 | 1,428 | 1,428 | 4,524 |

| Total | 3,336 | 2,856 | 2,856 | 9,048 |

Groups per bucket: 3,336 mono groups (1 location each), 857 small groups, 166 large groups. Large-cell brand diversity is low by design (~5 to 8 brands per cell).

**## By industry x region**

All six non-travel industries sit at exactly 714 per region (238 x 3 buckets). Travel is 240 per region, mono only. Its small and large cells were structurally starved and dropped (decision 2026-07-30).

| Industry | US | EU |

| --- | --- | --- |

| Automotive | 714 | 714 |

| Food & Beverage | 714 | 714 |

| Healthcare | 714 | 714 |

| Home services | 714 | 714 |

| Hospitality | 714 | 714 |

| Wellness & Fitness | 714 | 714 |

| Travel (mono only) | 240 | 240 |

**## By review count**

The review count drives the monitoring crawl load.

| Metric | Value |

| --- | --- |

| Median | 231 |

| Mean | 532 |

| p10 | 56 |

| p25 | 105 |

| p75 | 564 |

| p90 | 1,273 |

| Max | 24,041 |

| Total reviews in panel | ~4.81M |

| Review count band | Locations |

| --- | --- |

| Under 100 | 2,096 |

| 100 to 250 | 2,667 |

| 250 to 500 | 1,769 |

| 500 to 1k | 1,295 |

| 1k to 2.5k | 899 |

| 2.5k to 5k | 256 |

| 5k to 10k | 66 |

Note: some counts fall outside the 100 to 10,000 gate (min 0, max 24k). This is expected. The gate applies only to each group's seed location; siblings are never dropped, so a few sit below 100 or above 10k.

**## Sample for team review**

`docs/review_sample_100.csv`, 100 locations balanced round-robin across all 38 cells (2 to 3 per cell).

Columns: name, industry, subcategory, country, region, bucket, review_count, rating, maps_url, cluster_key, place_id, lat, lng.

The `maps_url` column is a direct place_id link. Click through to verify each match resolves to the right business.

This is a sample of panel locations, not scraped review text. The baseline crawl (wave 1) has not run yet, so there are no individual reviews to show.