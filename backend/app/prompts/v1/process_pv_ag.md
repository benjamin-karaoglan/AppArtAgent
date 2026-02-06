---
name: Process PV d'AG (Vision)
version: v1
description: Prompt for processing PV d'AG documents with vision capabilities
---

Analyze this PV d'AG (copropriété general assembly minutes) and extract:
- Meeting date
- Key decisions made
- Upcoming works and their estimated costs
- Any issues with copropriétaires (payment issues, disputes)
- Charges and fees mentioned
- Important deadlines

Return a JSON object with these fields:
{{
  "summary": "Brief summary of the meeting",
  "key_insights": ["insight 1", "insight 2"],
  "estimated_annual_cost": 1234.56,
  "one_time_costs": [{{"description": "Work description", "amount": 1000}}],
  "meeting_date": "2024-01-15",
  "decisions": ["decision 1", "decision 2"],
  "upcoming_works": [{{"description": "Work", "cost": 5000, "timeline": "Q2 2024"}}]
}}

IMPORTANT: Generate all text output (summary, key_findings, recommendations, issues, descriptions) in {output_language}.
