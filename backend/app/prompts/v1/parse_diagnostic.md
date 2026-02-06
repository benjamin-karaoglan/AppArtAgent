---
name: Parse Diagnostic Multimodal
version: v1
description: Prompt for multimodal parsing of diagnostic documents
---

Analyze this {subcategory} diagnostic and return JSON:
{{
    "diagnostic_date": "YYYY-MM-DD or null",
    "summary": "2-3 sentence summary",
    "key_insights": ["insight1", "insight2", "insight3"],
    "compliance_status": "compliant/non-compliant/needs-work",
    "issues_found": [{{"issue": "...", "severity": "critical/major/minor", "estimated_fix_cost": 0}}],
    "ratings": {{"dpe_rating": "A-G or null", "ges_rating": "A-G or null"}},
    "estimated_annual_cost": 0,
    "one_time_costs": [{{"item": "...", "amount": 0, "urgency": "high/medium/low"}}],
    "recommendations": []
}}

IMPORTANT: Generate all text output (summary, key_insights, descriptions, recommendations) in {output_language}.
