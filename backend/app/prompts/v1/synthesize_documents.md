---
name: Document Synthesis
version: v1
description: Prompt for synthesizing results from multiple property documents
---

You are synthesizing results from multiple property documents.

Documents processed:
{documents_json}

Create a comprehensive synthesis that:
1. Aggregates costs across all documents (annual costs, one-time costs)
2. Identifies key risks and concerns
3. Provides overall property assessment
4. Highlights any inconsistencies between documents
5. Gives actionable recommendations

Return a JSON object with this structure:
{{
  "summary": "Executive summary of all documents",
  "total_annual_costs": 0,
  "total_one_time_costs": 0,
  "risk_level": "low|medium|high",
  "key_findings": ["finding1", "finding2"],
  "recommendations": ["rec1", "rec2"],
  "documents_by_category": {{
    "pv_ag": {{"count": 0, "summary": ""}},
    "diagnostic": {{"count": 0, "summary": ""}},
    "taxe_fonciere": {{"count": 0, "summary": ""}},
    "charges": {{"count": 0, "summary": ""}}
  }}
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations, issues, descriptions) in {output_language}.
