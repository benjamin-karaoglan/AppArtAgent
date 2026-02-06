---
name: Document Processor - Process Diagnostic
version: v1
description: Prompt for processing diagnostic documents in the document processor pipeline
---

Analyze this diagnostic: {filename}

Extract JSON:
{{
  "summary": "Brief summary",
  "subcategory": "DPE/amiante/plomb/termites/gaz/electricite",
  "key_insights": ["insight1", "insight2"],
  "diagnostic_date": "YYYY-MM-DD or null",
  "issues_found": ["issue1", "issue2"],
  "recommendations": ["recommendation1"],
  "estimated_annual_cost": 0.0,
  "one_time_costs": 0.0
}}

IMPORTANT: Generate all text output (summary, key_insights, decisions, recommendations) in {output_language}.
