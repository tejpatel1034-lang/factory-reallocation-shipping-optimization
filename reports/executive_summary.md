# Executive Summary — Factory Reallocation & Shipping Optimization
**Nassau Candy Distributor** · 10,194 orders · 15 products · 5 factories · 2024–2025

## The question
Nassau Candy assigns products to factories using static legacy rules. Can data tell us where to produce each product to ship faster and cheaper — without hurting profit?

## What we found
- **Five factories serve every region, but assignments ignore customer geography.** Every product ships to all four regions regardless of factory location (e.g. Sugar Shack in Minnesota serves the Gulf and Pacific coasts).
- **Reassigning products to a closer factory cuts shipping distance by ~28% on average** across the best recommendation for each product × region pair, and 79% of recommendations show a freight saving (proxy model).
- **Profit is concentrated in five Wonka Bar products** (~95% of gross profit). Small distance gains on these produce the largest dollar savings — they are the priority for pilots.
- **Capacity is the main risk.** 23 of 53 recommendations would add >25% volume to the receiving factory and are flagged High risk; 29 are Low risk and can be piloted first.

## Important caveat (please read)
In the supplied data, **recorded lead time shows no meaningful relationship with distance, ship mode, region, or factory** (the model explains ~0% of variation beyond a year-level shift — ship dates appear to be system-generated). Therefore:
- Distance and freight-cost savings are **model-based estimates from geography**, not proven lead-time gains.
- Predicted lead-time reductions (~0.2%) should **not** be quoted as a business benefit.
- Validate with real shipment timestamps and actual freight rates before large-scale moves.

## Recommendation
1. **Pilot Low-risk reassignments** (29 of 53) for the top-profit Wonka Bar products in 1–2 regions.
2. **Check factory capacity** before any High-risk move.
3. **Capture clean ship/delivery timestamps and freight costs** so the model can learn true lead-time drivers.
4. Use the Streamlit dashboard to re-run scenarios as the speed-vs-profit priority changes.
