---
name: Process Charges (Vision)
version: v1
description: Prompt for processing charges documents with vision capabilities
---

Analyze this charges/copropriété fees document and extract:
- Period covered
- Total charges
- Breakdown by category (if available)
- Any special assessments

Return a JSON object with these fields:
{{
  "summary": "Brief summary",
  "period": "2024",
  "total_charges": 2400,
  "estimated_annual_cost": 2400,
  "breakdown": {{"heating": 1000, "maintenance": 800, "other": 600}},
  "key_insights": ["insight 1"]
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations, issues, descriptions) in {output_language}.
