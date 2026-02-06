---
name: Document Processor - Synthesize Results
version: v1
description: Prompt for synthesizing results from multiple processed documents
---

Synthesize these property documents:

{summaries}

Return JSON:
{{
  "summary": "Overall summary (2-3 sentences)",
  "total_annual_costs": 0.0,
  "total_one_time_costs": 0.0,
  "risk_level": "low/medium/high",
  "key_findings": ["finding1", "finding2", "finding3"],
  "recommendations": ["recommendation1", "recommendation2"]
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations) in {output_language}.
