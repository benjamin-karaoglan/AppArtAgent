---
name: Diagnostic Analysis
version: v1
description: Prompt for analyzing French property diagnostic documents
---

Analyze the following French property diagnostic document.

Extract and identify:
1. DPE (Energy Performance) rating (A-G)
2. GES (Greenhouse Gas) rating (A-G)
3. Energy consumption (kWh/m²/year)
4. Presence of amiante (asbestos)
5. Presence of plomb (lead)
6. Other risk factors or issues
7. Estimated renovation costs to improve rating
8. Specific recommendations for the buyer

Document text:
{document_text}

Provide your analysis in JSON format with the following structure:
{{
    "dpe_rating": "A-G or null",
    "ges_rating": "A-G or null",
    "energy_consumption": 0,
    "has_amiante": true/false,
    "has_plomb": true/false,
    "risk_flags": ["flag1", "flag2"],
    "estimated_renovation_cost": 0,
    "summary": "Brief summary",
    "recommendations": ["recommendation 1", "recommendation 2"]
}}
