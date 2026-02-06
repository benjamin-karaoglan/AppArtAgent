---
name: Document Processor - Process PV AG
version: v1
description: Prompt for processing PV d'AG documents in the document processor pipeline
---

Analyze this PV AG: {filename}

Extract JSON:
{{
  "summary": "Brief summary",
  "key_insights": ["insight1", "insight2"],
  "meeting_date": "YYYY-MM-DD or null",
  "decisions": ["decision1", "decision2"],
  "votes": [{{"topic": "...", "result": "approved/rejected"}}],
  "estimated_annual_cost": 0.0,
  "one_time_costs": 0.0
}}

IMPORTANT: Generate all text output (summary, key_insights, decisions, recommendations) in {output_language}.
