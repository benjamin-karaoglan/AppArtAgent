---
name: PV d'AG Analysis
version: v1
description: Prompt for analyzing French copropriété assembly meeting minutes
---

Analyze the following French copropriété assembly meeting minutes (PV d'AG).

Extract and identify:
1. All upcoming works mentioned (travaux à venir)
2. Estimated costs for each work item
3. Financial health of the copropriété (budget, reserves, debts)
4. Any disputes or issues mentioned
5. Risk level for the buyer (low, medium, high)
6. Key findings that would impact a purchase decision
7. Specific recommendations for the buyer

Document text:
{document_text}

Provide your analysis in JSON format with the following structure:
{{
    "summary": "Brief overall summary",
    "upcoming_works": [
        {{"description": "work description", "estimated_cost": 0, "timeline": "when"}}
    ],
    "financial_health": {{
        "budget_status": "description",
        "reserves": 0,
        "outstanding_debts": 0,
        "health_score": 0-100
    }},
    "risk_level": "low|medium|high",
    "key_findings": ["finding 1", "finding 2"],
    "recommendations": ["recommendation 1", "recommendation 2"]
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations, issues, descriptions) in {output_language}.
