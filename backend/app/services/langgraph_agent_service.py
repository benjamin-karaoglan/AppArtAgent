"""
LangGraph agent service for intelligent document classification and routing.

This service uses LangGraph to orchestrate document processing workflows:
1. Classify uploaded documents (PV AG, diagnostics, taxes, charges)
2. Route to specialized processing agents
3. Process documents in parallel
4. Synthesize results across multiple documents
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Annotated, TypedDict
from operator import add
import json

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings

logger = logging.getLogger(__name__)


# Define the state for our agent graph
class DocumentProcessingState(TypedDict):
    """State for the document processing workflow."""
    # Input
    documents: List[Dict[str, Any]]  # List of {filename, file_data_base64, property_id}
    property_id: int

    # Classification results
    classified_documents: Annotated[List[Dict[str, Any]], add]  # {filename, doc_type, confidence}

    # Processing results
    processing_results: Annotated[List[Dict[str, Any]], add]  # Individual document results

    # Synthesis
    synthesis: Dict[str, Any]  # Final aggregated results

    # Metadata
    errors: Annotated[List[str], add]
    total_tokens: int
    total_cost: float


class LangGraphDocumentAgent:
    """
    LangGraph-based document processing agent.

    This agent orchestrates the entire document processing pipeline:
    - Classifies documents by type
    - Routes to specialized processing
    - Runs parallel processing
    - Synthesizes results
    """

    def __init__(self):
        """Initialize the LangGraph agent."""
        logger.info("Initializing LangGraph Document Agent")

        # Initialize Claude model
        self.llm = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=0,
        )

        # Build the workflow graph
        self.workflow = self._build_workflow()

        # Add memory for checkpointing
        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)

        logger.info("LangGraph Document Agent initialized successfully")

    def export_graph_as_png(self, output_path: str = None) -> str:
        """
        Export the LangGraph workflow as a PNG image.

        Args:
            output_path: Optional path to save the PNG. If not provided, saves to ./langgraph_workflow.png

        Returns:
            Path to the saved PNG file
        """
        if output_path is None:
            output_path = "langgraph_workflow.png"

        try:
            # Get the graph as a Mermaid diagram PNG
            mermaid_png = self.app.get_graph().draw_mermaid_png()

            # Save to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(mermaid_png)

            logger.info(f"LangGraph workflow saved to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export graph as PNG: {e}")
            # Fallback: try ASCII representation
            try:
                ascii_graph = self.app.get_graph().print_ascii()
                txt_path = output_path.with_suffix('.txt') if isinstance(output_path, Path) else Path(output_path).with_suffix('.txt')
                with open(txt_path, 'w') as f:
                    f.write(ascii_graph)
                logger.info(f"Saved ASCII graph to {txt_path} (PNG export failed)")
                return str(txt_path)
            except Exception as e2:
                logger.error(f"Failed to export ASCII graph: {e2}")
                raise

    def get_graph_ascii(self) -> str:
        """
        Get ASCII representation of the workflow graph.

        Returns:
            ASCII art representation of the graph
        """
        try:
            return self.app.get_graph().print_ascii()
        except Exception as e:
            logger.error(f"Failed to get ASCII graph: {e}")
            return f"Error generating graph: {str(e)}"

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(DocumentProcessingState)

        # Add nodes
        workflow.add_node("classify_documents", self.classify_documents_node)
        workflow.add_node("process_pv_ag", self.process_pv_ag_node)
        workflow.add_node("process_diagnostic", self.process_diagnostic_node)
        workflow.add_node("process_tax", self.process_tax_node)
        workflow.add_node("process_charges", self.process_charges_node)
        workflow.add_node("synthesize_results", self.synthesize_results_node)

        # Define the flow
        workflow.set_entry_point("classify_documents")

        # After classification, route to appropriate processors
        workflow.add_conditional_edges(
            "classify_documents",
            self.route_documents,
            {
                "process_pv_ag": "process_pv_ag",
                "process_diagnostic": "process_diagnostic",
                "process_tax": "process_tax",
                "process_charges": "process_charges",
                "synthesize": "synthesize_results",
            }
        )

        # All processors flow to synthesis
        workflow.add_edge("process_pv_ag", "synthesize_results")
        workflow.add_edge("process_diagnostic", "synthesize_results")
        workflow.add_edge("process_tax", "synthesize_results")
        workflow.add_edge("process_charges", "synthesize_results")

        # Synthesis is the end
        workflow.add_edge("synthesize_results", END)

        return workflow

    def classify_documents_node(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """
        Classify each uploaded document to determine its type.

        Uses Claude to analyze the first page of each document and classify it.
        """
        logger.info(f"Classifying {len(state['documents'])} documents")

        classified = []
        total_tokens = 0
        total_cost = 0.0

        for doc in state['documents']:
            try:
                # Create classification prompt
                messages = [
                    SystemMessage(content="""You are a document classification expert for French real estate documents.

Classify the document into ONE of these categories:
- pv_ag: PV d'Assemblée Générale (copropriété meeting minutes)
- diagnostic: Diagnostic reports (DPE, amiante, plomb, termites, électricité, gaz)
- taxe_fonciere: Taxe foncière (property tax)
- charges: Charges de copropriété (copropriété fees/charges)
- other: Other documents

Return ONLY a JSON object with this structure:
{
  "document_type": "pv_ag|diagnostic|taxe_fonciere|charges|other",
  "confidence": 0.0-1.0,
  "subtype": "optional subtype like 'DPE', 'amiante', etc",
  "reasoning": "brief explanation"
}"""),
                    HumanMessage(content=[
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": doc["file_data_base64"][0]  # First page only for classification
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Classify this document. Filename: {doc['filename']}"
                        }
                    ])
                ]

                response = self.llm.invoke(messages)

                # Parse response
                response_text = response.content
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                result = json.loads(response_text)

                classified.append({
                    "filename": doc["filename"],
                    "document_type": result["document_type"],
                    "subtype": result.get("subtype"),
                    "confidence": result["confidence"],
                    "reasoning": result["reasoning"],
                    "file_data_base64": doc["file_data_base64"],
                    "property_id": doc["property_id"]
                })

                # Track tokens (approximate)
                total_tokens += response.usage_metadata.get("total_tokens", 0) if hasattr(response, 'usage_metadata') else 0

                logger.info(f"Classified {doc['filename']} as {result['document_type']} (confidence: {result['confidence']})")

            except Exception as e:
                logger.error(f"Error classifying document {doc['filename']}: {e}")
                classified.append({
                    "filename": doc["filename"],
                    "document_type": "other",
                    "confidence": 0.0,
                    "error": str(e)
                })

        return {
            "classified_documents": classified,
            "total_tokens": total_tokens,
            "total_cost": total_cost
        }

    def route_documents(self, state: DocumentProcessingState) -> str:
        """
        Decide which processing node to execute next based on classified documents.

        Returns the name of the next node to execute.
        """
        classified = state.get("classified_documents", [])

        # Check which document types we have
        doc_types = {doc["document_type"] for doc in classified}

        # Priority order: pv_ag > diagnostic > tax > charges
        if "pv_ag" in doc_types:
            return "process_pv_ag"
        elif "diagnostic" in doc_types:
            return "process_diagnostic"
        elif "taxe_fonciere" in doc_types:
            return "process_tax"
        elif "charges" in doc_types:
            return "process_charges"
        else:
            # No recognized documents, go straight to synthesis
            return "synthesize"

    def process_pv_ag_node(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """Process PV d'AG documents."""
        logger.info("Processing PV d'AG documents")

        classified = state.get("classified_documents", [])
        pv_ag_docs = [doc for doc in classified if doc["document_type"] == "pv_ag"]

        results = []

        for doc in pv_ag_docs:
            try:
                result = self._process_single_document(
                    doc["file_data_base64"],
                    "pv_ag",
                    doc["filename"]
                )
                results.append({
                    "filename": doc["filename"],
                    "document_type": "pv_ag",
                    "result": result
                })
                logger.info(f"Processed PV AG: {doc['filename']}")
            except Exception as e:
                logger.error(f"Error processing PV AG {doc['filename']}: {e}")
                results.append({
                    "filename": doc["filename"],
                    "document_type": "pv_ag",
                    "error": str(e)
                })

        return {"processing_results": results}

    def process_diagnostic_node(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """Process diagnostic documents."""
        logger.info("Processing diagnostic documents")

        classified = state.get("classified_documents", [])
        diagnostic_docs = [doc for doc in classified if doc["document_type"] == "diagnostic"]

        results = []

        for doc in diagnostic_docs:
            try:
                result = self._process_single_document(
                    doc["file_data_base64"],
                    "diagnostic",
                    doc["filename"],
                    subtype=doc.get("subtype")
                )
                results.append({
                    "filename": doc["filename"],
                    "document_type": "diagnostic",
                    "subtype": doc.get("subtype"),
                    "result": result
                })
                logger.info(f"Processed diagnostic: {doc['filename']}")
            except Exception as e:
                logger.error(f"Error processing diagnostic {doc['filename']}: {e}")
                results.append({
                    "filename": doc["filename"],
                    "document_type": "diagnostic",
                    "error": str(e)
                })

        return {"processing_results": results}

    def process_tax_node(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """Process tax documents."""
        logger.info("Processing tax documents")

        classified = state.get("classified_documents", [])
        tax_docs = [doc for doc in classified if doc["document_type"] == "taxe_fonciere"]

        results = []

        for doc in tax_docs:
            try:
                result = self._process_single_document(
                    doc["file_data_base64"],
                    "taxe_fonciere",
                    doc["filename"]
                )
                results.append({
                    "filename": doc["filename"],
                    "document_type": "taxe_fonciere",
                    "result": result
                })
                logger.info(f"Processed tax: {doc['filename']}")
            except Exception as e:
                logger.error(f"Error processing tax {doc['filename']}: {e}")
                results.append({
                    "filename": doc["filename"],
                    "document_type": "taxe_fonciere",
                    "error": str(e)
                })

        return {"processing_results": results}

    def process_charges_node(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """Process charges documents."""
        logger.info("Processing charges documents")

        classified = state.get("classified_documents", [])
        charges_docs = [doc for doc in classified if doc["document_type"] == "charges"]

        results = []

        for doc in charges_docs:
            try:
                result = self._process_single_document(
                    doc["file_data_base64"],
                    "charges",
                    doc["filename"]
                )
                results.append({
                    "filename": doc["filename"],
                    "document_type": "charges",
                    "result": result
                })
                logger.info(f"Processed charges: {doc['filename']}")
            except Exception as e:
                logger.error(f"Error processing charges {doc['filename']}: {e}")
                results.append({
                    "filename": doc["filename"],
                    "document_type": "charges",
                    "error": str(e)
                })

        return {"processing_results": results}

    def synthesize_results_node(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """
        Synthesize all processing results into a coherent summary.

        This is especially important when there are multiple PV d'AG or multiple diagnostics.
        """
        logger.info("Synthesizing results across all documents")

        results = state.get("processing_results", [])

        if not results:
            return {
                "synthesis": {
                    "summary": "No documents were successfully processed",
                    "documents_processed": 0
                }
            }

        # Group by document type
        by_type = {}
        for result in results:
            doc_type = result["document_type"]
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result)

        # Create synthesis prompt
        synthesis_prompt = f"""You are synthesizing results from multiple property documents.

Documents processed:
{json.dumps(results, indent=2)}

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
}}"""

        try:
            messages = [
                SystemMessage(content="You are a real estate analysis expert. Synthesize document results into actionable insights."),
                HumanMessage(content=synthesis_prompt)
            ]

            response = self.llm.invoke(messages)
            response_text = response.content

            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            synthesis = json.loads(response_text)

            logger.info("Synthesis complete")

            return {"synthesis": synthesis}

        except Exception as e:
            logger.error(f"Error synthesizing results: {e}")
            return {
                "synthesis": {
                    "summary": f"Error during synthesis: {str(e)}",
                    "documents_processed": len(results),
                    "error": str(e)
                }
            }

    def _process_single_document(
        self,
        images_base64: List[str],
        document_type: str,
        filename: str,
        subtype: str = None
    ) -> Dict[str, Any]:
        """
        Process a single document with Claude vision.

        This uses the same prompts as in activities.py but through LangChain.
        """
        # Get the appropriate prompt
        prompt = self._get_prompt_for_document_type(document_type, subtype)

        # Build messages with all pages
        content_parts = []
        for img_base64 in images_base64:
            content_parts.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })

        content_parts.append({
            "type": "text",
            "text": prompt
        })

        messages = [
            SystemMessage(content="You are an expert at analyzing French real estate documents. Extract all relevant information accurately."),
            HumanMessage(content=content_parts)
        ]

        response = self.llm.invoke(messages)
        response_text = response.content

        # Parse JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        parsed_data = json.loads(response_text)

        return {
            "parsed_data": parsed_data,
            "tokens_used": response.usage_metadata.get("total_tokens", 0) if hasattr(response, 'usage_metadata') else 0,
            "model": settings.ANTHROPIC_MODEL
        }

    def _get_prompt_for_document_type(self, document_type: str, subtype: str = None) -> str:
        """Get appropriate prompt template for document type."""
        prompts = {
            "pv_ag": """Analyze this PV d'AG (copropriété general assembly minutes) and extract:
- Meeting date
- Key decisions made
- Upcoming works and their estimated costs
- Any issues with copropriétaires (payment issues, disputes)
- Charges and fees mentioned
- Important deadlines

Return a JSON object with these fields:
{
  "summary": "Brief summary of the meeting",
  "key_insights": ["insight 1", "insight 2"],
  "estimated_annual_cost": 1234.56,
  "one_time_costs": [{"description": "Work description", "amount": 1000}],
  "meeting_date": "2024-01-15",
  "decisions": ["decision 1", "decision 2"],
  "upcoming_works": [{"description": "Work", "cost": 5000, "timeline": "Q2 2024"}]
}""",

            "diagnostic": """Analyze this diagnostic report and extract:
- Type of diagnostic (DPE, amiante, plomb, termites, electric, gas)
- Date of the diagnostic
- Overall result/rating
- Any issues or non-compliances found
- Recommendations
- Estimated costs for remediation

Return a JSON object with these fields:
{
  "summary": "Brief summary",
  "key_insights": ["insight 1", "insight 2"],
  "diagnostic_type": "DPE",
  "diagnostic_date": "2024-01-15",
  "rating": "C",
  "issues_found": ["issue 1", "issue 2"],
  "estimated_annual_cost": 0,
  "one_time_costs": [{"description": "Remediation", "amount": 2000}]
}""",

            "taxe_fonciere": """Analyze this taxe foncière document and extract:
- Year
- Total amount
- Property value (valeur cadastrale)
- Any exemptions or reductions

Return a JSON object with these fields:
{
  "summary": "Brief summary",
  "year": 2024,
  "total_amount": 1234.56,
  "property_value": 50000,
  "estimated_annual_cost": 1234.56,
  "key_insights": ["insight 1"]
}""",

            "charges": """Analyze this charges/copropriété fees document and extract:
- Period covered
- Total charges
- Breakdown by category (if available)
- Any special assessments

Return a JSON object with these fields:
{
  "summary": "Brief summary",
  "period": "2024",
  "total_charges": 2400,
  "estimated_annual_cost": 2400,
  "breakdown": {"heating": 1000, "maintenance": 800, "other": 600},
  "key_insights": ["insight 1"]
}"""
        }

        return prompts.get(document_type, prompts["diagnostic"])

    async def process_bulk_upload(
        self,
        documents: List[Dict[str, Any]],
        property_id: int,
        thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Process multiple documents in bulk using the LangGraph workflow.

        Args:
            documents: List of {filename, file_data_base64} dicts
            property_id: Property ID for these documents
            thread_id: Optional thread ID for checkpointing

        Returns:
            Final state with synthesis
        """
        logger.info(f"Processing bulk upload: {len(documents)} documents for property {property_id}")

        # Prepare initial state
        initial_state = {
            "documents": [
                {**doc, "property_id": property_id}
                for doc in documents
            ],
            "property_id": property_id,
            "classified_documents": [],
            "processing_results": [],
            "synthesis": {},
            "errors": [],
            "total_tokens": 0,
            "total_cost": 0.0
        }

        # Configure execution
        config = {"configurable": {"thread_id": thread_id or f"property_{property_id}"}}

        # Run the workflow
        final_state = None
        for state in self.app.stream(initial_state, config):
            final_state = state
            logger.debug(f"Workflow state: {list(state.keys())}")

        logger.info(f"Bulk upload complete for property {property_id}")

        return final_state


# Singleton instance
_langgraph_agent_instance = None


def get_langgraph_agent() -> LangGraphDocumentAgent:
    """Get or create the LangGraph document agent singleton."""
    global _langgraph_agent_instance
    if _langgraph_agent_instance is None:
        _langgraph_agent_instance = LangGraphDocumentAgent()
    return _langgraph_agent_instance
