---
name: Document Processor - Process Charges
version: v1
description: Prompt for processing charges documents in the document processor pipeline
---

Analyze this charges document: {filename}

Extract JSON:
{{
  "summary": "Brief summary",
  "key_insights": ["insight1", "insight2"],
  "period": "Q1 2024 or similar",
  "total_amount": 0.0,
  "breakdown": [{{"category": "...", "amount": 0.0}}],
  "estimated_annual_cost": 0.0,
  "one_time_costs": 0.0
}}

IMPORTANT: Generate all text output (summary, key_insights, decisions, recommendations) in {output_language}.
