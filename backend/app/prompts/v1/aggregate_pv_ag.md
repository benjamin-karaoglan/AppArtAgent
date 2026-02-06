---
name: Aggregate PV d'AG Summaries
version: v1
description: Prompt for synthesizing multiple PV d'AG documents into one summary
---

Synthesize these PV d'AG documents into JSON:
{documents_json}

Return JSON:
{{
    "summary": "Overall summary",
    "key_findings": [],
    "copropriete_insights": {{}},
    "total_estimated_annual_cost": 0,
    "total_one_time_costs": 0,
    "cost_breakdown": {{}},
    "recommendations": []
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations) in {output_language}.
