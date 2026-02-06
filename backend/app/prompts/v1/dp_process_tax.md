---
name: Document Processor - Process Tax
version: v1
description: Prompt for processing taxe foncière documents in the document processor pipeline
---

Analyze this taxe foncière: {filename}

Extract JSON:
{{
  "summary": "Brief summary",
  "key_insights": ["insight1", "insight2"],
  "tax_year": "YYYY or null",
  "total_amount": 0.0,
  "due_date": "YYYY-MM-DD or null",
  "estimated_annual_cost": 0.0,
  "one_time_costs": 0.0
}}

IMPORTANT: Generate all text output (summary, key_insights, decisions, recommendations) in {output_language}.
