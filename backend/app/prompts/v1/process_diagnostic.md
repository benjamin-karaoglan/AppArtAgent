---
name: Process Diagnostic (Vision)
version: v1
description: Prompt for processing diagnostic documents with vision capabilities
---

Analyze this diagnostic report and extract:
- Type of diagnostic (DPE, amiante, plomb, termites, electric, gas)
- Date of the diagnostic
- Overall result/rating
- Any issues or non-compliances found
- Recommendations
- Estimated costs for remediation

Return a JSON object with these fields:
{{
  "summary": "Brief summary",
  "key_insights": ["insight 1", "insight 2"],
  "diagnostic_type": "DPE",
  "diagnostic_date": "2024-01-15",
  "rating": "C",
  "issues_found": ["issue 1", "issue 2"],
  "estimated_annual_cost": 0,
  "one_time_costs": [{{"description": "Remediation", "amount": 2000}}]
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations, issues, descriptions) in {output_language}.
