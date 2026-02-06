---
name: Parse PV d'AG Multimodal
version: v1
description: Prompt for multimodal parsing of PV d'AG documents
---

Analyze this PV d'AG and return JSON:
{{
    "meeting_date": "YYYY-MM-DD or null",
    "summary": "2-3 sentence summary",
    "key_insights": ["insight1", "insight2", "insight3"],
    "upcoming_works": [{{"description": "...", "estimated_cost": 0, "timeline": "...", "urgency": "high/medium/low"}}],
    "financial_health": {{"annual_budget": 0, "reserves": 0, "outstanding_debts": 0, "health_status": "good/fair/poor"}},
    "estimated_annual_cost": 0,
    "one_time_costs": [{{"item": "...", "amount": 0, "timeline": "..."}}],
    "risk_assessment": {{"overall_risk": "low/medium/high", "risk_factors": [], "recommendations": []}}
}}

IMPORTANT: Generate all text output (summary, key_insights, descriptions, recommendations) in {output_language}.
