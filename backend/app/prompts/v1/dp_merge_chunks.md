---
name: Document Processor - Merge Chunk Results
version: v1
description: Prompt for merging analysis results from multiple chunks of a single large document
---

You are merging the analysis results from multiple chunks of a SINGLE large document.

The document was too large to process at once, so it was split into {chunk_count} sequential page-range chunks and each chunk was analyzed independently. Your job is to combine these partial analyses into one coherent, unified analysis — as if the entire document had been processed at once.

**Document type**: {document_type}

Here are the chunk results in page order:

{chunk_results}

Merge these into a single JSON result with the same structure as an individual chunk result. Specifically:

- **summary**: Write a unified summary covering the FULL document (not a summary of summaries). Combine information from all chunks into a coherent narrative (3-5 sentences).
- **key_insights**: Merge and deduplicate insights from all chunks. Combine related insights that span chunks. Keep the most important 5-8 insights.
- **estimated_annual_cost**: Sum of all annual costs across chunks (avoid double-counting if the same cost appears in overlapping chunk boundaries).
- **one_time_costs**: Sum of all one-time costs across chunks (avoid double-counting).
- All other fields: Merge intelligently. If a field appears in multiple chunks with different values, use the most complete/recent value.

Rules:

- Information from later chunks (higher page numbers) takes precedence for dates and status fields
- Deduplicate items that appear in multiple chunks due to page boundary overlap
- Preserve all unique financial amounts — do not drop any
- If chunks disagree on a value, note the discrepancy in the relevant field

IMPORTANT: Generate all text output in {output_language}.
Return ONLY the JSON object, no surrounding text or markdown.
