---
name: Parse Tax/Charges Multimodal
version: v1
description: Prompt for multimodal parsing of tax or charges documents
---

Analyze this {doc_type} and return JSON:
{{
    "document_year": "YYYY",
    "summary": "2-3 sentence summary",
    "key_insights": ["insight1", "insight2"],
    "total_annual_amount": 0,
    "breakdown": {{}},
    "estimated_annual_cost": 0
}}

IMPORTANT: Generate all text output (summary, key_insights, descriptions) in {output_language}.
