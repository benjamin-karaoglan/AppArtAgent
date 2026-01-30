---
name: Tax/Charges Analysis
version: v1
description: Prompt for analyzing French property tax and charges documents
---

Analyze the following French property {document_type} document.

Extract:
1. Total amount charged
2. Period covered (e.g., "3 months", "annual", "quarterly")
3. Breakdown of charges by category
4. Calculate the annual amount (if period is less than 1 year, multiply accordingly)

Document text:
{document_text}

Provide your analysis in JSON format:
{{
    "period_covered": "description of period",
    "total_amount": 0,
    "annual_amount": 0,
    "breakdown": {{
        "category1": 0,
        "category2": 0
    }},
    "summary": "Brief summary"
}}
