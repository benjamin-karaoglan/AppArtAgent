---
name: Aggregate Diagnostic Summaries
version: v1
description: Prompt for synthesizing multiple diagnostic documents into one summary
---

Synthesize these diagnostics into JSON:
{documents_json}

Return JSON:
{{
    "summary": "Overall summary",
    "key_findings": [],
    "diagnostic_issues": {{}},
    "total_estimated_annual_cost": 0,
    "total_one_time_costs": 0,
    "recommendations": []
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations) in {output_language}.
