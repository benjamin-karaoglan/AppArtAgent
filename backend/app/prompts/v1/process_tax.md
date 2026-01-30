---
name: Process Taxe Foncière (Vision)
version: v1
description: Prompt for processing tax documents with vision capabilities
---

Analyze this taxe foncière document and extract:
- Year
- Total amount
- Property value (valeur cadastrale)
- Any exemptions or reductions

Return a JSON object with these fields:
{
  "summary": "Brief summary",
  "year": 2024,
  "total_amount": 1234.56,
  "property_value": 50000,
  "estimated_annual_cost": 1234.56,
  "key_insights": ["insight 1"]
}
