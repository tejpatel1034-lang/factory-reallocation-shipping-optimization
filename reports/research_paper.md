# A Predictive and Optimization-Based Framework for Factory Reallocation at Nassau Candy Distributor

## Abstract
We build a decision-intelligence system that (1) predicts shipping lead time under different factory configurations, (2) simulates reassigning products to alternative factories, and (3) ranks reassignments by operational gain, profit impact and risk. Using 10,194 orders (2024–2025), three regression models are compared. Findings show that the dataset's lead-time field carries almost no route-level signal, so recommendations are driven chiefly by geographic distance and a freight-cost proxy. Best-per-pair reassignments reduce average shipping distance by ~28%, with 79% showing positive freight impact.

## 1. Introduction
Nassau Candy fulfils orders from five factories using static product-to-factory rules. This leads to suboptimal distances, long lead times in some regions and margin erosion. The goal is a system leadership can use to answer: *what should we change to improve performance?*

## 2. Data
10,194 order lines, 15 products across Chocolate (9,844), Other (310) and Sugar (40) divisions; four regions (Pacific, Atlantic, Interior, Gulf); four ship modes; US and Canada. No missing values or duplicates. Factory coordinates and the product→factory map were supplied with the brief. Customer location is approximated by state/province centroid; distance is the haversine distance factory→centroid.

**EDA highlights** (see `reports/figures/`): profit is highly concentrated in five Wonka Bars; Standard Class carries 60% of orders; distance varies widely by product because factories are far apart.

## 3. Methodology
1. **Preparation** – lead time = Ship Date − Order Date; IQR outlier filter within each order year (no rows removed); one-hot encoding for product, factory, region, ship mode; standardised numeric features (distance, units, order year).
2. **Models** – Linear Regression (baseline), Random Forest, Gradient Boosting; 80/20 split; RMSE, MAE, R².
3. **Selection** – lowest RMSE, preferring the simpler model when within 2%.
4. **Simulation** – for a product, each order is re-scored as if produced at every factory (distance recomputed), yielding predicted lead time, distance and freight proxy (rate × units × km).
5. **Ranking** – score = w·operational gain + (1−w)·profit gain − risk penalty; risk from the receiving factory's volume increase.

## 4. Results
| Model | RMSE | MAE | R² | R² within year |
|---|---|---|---|---|
| Linear Regression | 182.6 | 181.5 | 0.529 | −0.006 |
| Gradient Boosting | 182.8 | 180.7 | 0.527 | −0.008 |
| Random Forest | 183.6 | 179.5 | 0.523 | −0.018 |

Linear Regression is selected (simplest, equal accuracy). R² ≈ 0.53 comes almost entirely from an order-year offset (2024 vs 2025 ship dates); **within-year R² ≈ 0** shows no usable signal from product, region, ship mode or distance.

**Recommendations (53 product×region pairs):** mean distance reduction 27.9%; 79.2% with freight saving; 70% coverage with both distance and profit gains; 29 Low, 1 Medium, 23 High risk. Most-recommended receivers: Secret Factory (22), The Other Factory (12).

## 5. Discussion & Limitations
- Lead time in the file is 900–1,640 days with ship dates in 2026–2030, indicating synthetic or mis-keyed dates. It cannot support causal lead-time claims.
- No freight cost or factory capacity data was provided; both are assumptions in `src/config.py`.
- State-centroid distances ignore carrier networks and ship-mode transit times.
- Simulated factories have never produced the product, so extrapolation is unavoidable; the confidence score reports how many simulated routes fall within the observed distance range.

## 6. Conclusion
The framework turns descriptive analytics into scenario-based recommendations. Geographic reassignment promises meaningful distance and freight savings, but lead-time benefits remain unproven until reliable shipment timestamps are available. Pilot Low-risk moves first.
