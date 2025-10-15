---
name: Build request (Auto-PR)
about: Ask the Auto-PR Agent to make changes
title: "[BUILD] <short title>"
labels: ["build"]
---

## What do you want?
Explain in plain English (e.g., “Add Utilization chart to Asset Management tab. Show top 10 assets, color badges, tooltip text from spec.”)

## Which tab / intent?
- intent: <e.g., asset_management>

## What data should it use?
- e.g., profile goals, QuickBooks fields, peer priors

## Acceptance criteria
- [ ] New UI renders without errors
- [ ] JSON matches ai/tabs/<intent>.yaml output_schema
- [ ] Basic tests updated/added if needed

## Screens / files you expect touched (optional)
- frontend/pages/...
- backend/routes/...
- ai/tabs/<intent>.yaml
