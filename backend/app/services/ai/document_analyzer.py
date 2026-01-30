"""
Document Analyzer - AI-powered document analysis using Gemini.

Provides text and vision-based document analysis, classification,
and synthesis capabilities using Google's Gemini models.
"""

import logging
import time
import json
import base64
from typing import Dict, Any, List, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.prompts import get_prompt, get_system_prompt

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    AI service for document analysis using Gemini.

    Capabilities:
    - Text-based document analysis (PV AG, diagnostics, taxes, charges)
    - Vision/multimodal document processing
    - Document classification
    - Multi-document synthesis
    - Property report generation
    """

    def __init__(self):
        """Initialize Gemini client."""
        logger.info("Initializing DocumentAnalyzer")

        self.use_vertexai = settings.GEMINI_USE_VERTEXAI
        self.model = settings.GEMINI_LLM_MODEL
        self.project = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_LOCATION

        if self.use_vertexai:
            if not self.project:
                raise RuntimeError("GOOGLE_CLOUD_PROJECT required for Vertex AI")
            self.client = genai.Client(
                vertexai=True,
                project=self.project,
                location=self.location
            )
        else:
            api_key = settings.GOOGLE_CLOUD_API_KEY
            if not api_key:
                raise RuntimeError("GOOGLE_CLOUD_API_KEY required for Gemini API")
            self.client = genai.Client(api_key=api_key)

        logger.info(f"Using model: {self.model}")

    def _extract_text(self, response) -> str:
        """Extract text from Gemini response."""
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return ""
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None) or []
        return "\n".join(p.text for p in parts if getattr(p, "text", None)).strip()

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        return json.loads(json_str)

    def _get_config(self, max_tokens: int = 4096, temperature: float = 0.1) -> types.GenerateContentConfig:
        """Get generation configuration."""
        return types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=max_tokens,
        )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1
    ) -> str:
        """Generate text response from Gemini."""
        start_time = time.time()

        try:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=full_prompt)])]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=self._get_config(max_tokens, temperature),
            )

            result = self._extract_text(response)
            logger.debug(f"Generated response in {int((time.time() - start_time) * 1000)}ms")
            return result

        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            raise

    async def analyze_with_vision(
        self,
        images_base64: List[str],
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Analyze images with text prompt using Gemini vision."""
        start_time = time.time()

        try:
            parts = []
            for img_b64 in images_base64:
                img_bytes = base64.b64decode(img_b64)
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))

            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            parts.append(types.Part.from_text(text=full_prompt))

            response = self.client.models.generate_content(
                model=self.model,
                contents=[types.Content(role="user", parts=parts)],
                config=self._get_config(max_tokens),
            )

            result = self._parse_json_response(self._extract_text(response))
            logger.debug(f"Vision analysis completed in {int((time.time() - start_time) * 1000)}ms")
            return result

        except Exception as e:
            logger.error(f"Error in vision analysis: {e}", exc_info=True)
            raise

    async def analyze_pvag_document(self, document_text: str) -> Dict[str, Any]:
        """Analyze PV d'AG (Assembly General Meeting Minutes)."""
        logger.info(f"Analyzing PV d'AG, length: {len(document_text)}")
        prompt = get_prompt("analyze_pvag", document_text=document_text)
        response_text = await self.generate_text(prompt)
        return self._parse_json_response(response_text)

    async def analyze_diagnostic_document(self, document_text: str) -> Dict[str, Any]:
        """Analyze diagnostic documents (DPE, amiante, plomb)."""
        logger.info(f"Analyzing diagnostic, length: {len(document_text)}")
        prompt = get_prompt("analyze_diagnostic", document_text=document_text)
        response_text = await self.generate_text(prompt)
        return self._parse_json_response(response_text)

    async def analyze_tax_charges_document(self, document_text: str, document_type: str) -> Dict[str, Any]:
        """Analyze tax or charges documents."""
        logger.info(f"Analyzing {document_type}, length: {len(document_text)}")
        prompt = get_prompt("analyze_tax_charges", document_text=document_text, document_type=document_type)
        response_text = await self.generate_text(prompt)
        result = self._parse_json_response(response_text)
        result["document_type"] = document_type
        return result

    async def analyze_property_photos(self, image_data: bytes, transformation_request: str) -> Dict[str, Any]:
        """Analyze property photos for style transformation suggestions."""
        logger.info(f"Analyzing property photo, size: {len(image_data)} bytes")
        prompt = get_prompt("analyze_photo", transformation_request=transformation_request)

        parts = [
            types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
            types.Part.from_text(text=prompt)
        ]

        response = self.client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=parts)],
            config=self._get_config(),
        )

        return {
            "analysis": self._extract_text(response),
            "transformation_request": transformation_request
        }

    async def generate_property_report(
        self,
        property_data: Dict[str, Any],
        price_analysis: Dict[str, Any],
        documents_analysis: List[Dict[str, Any]]
    ) -> str:
        """Generate comprehensive property analysis report."""
        logger.info("Generating property report")
        prompt = get_prompt(
            "generate_property_report",
            property_data=json.dumps(property_data, indent=2),
            price_analysis=json.dumps(price_analysis, indent=2),
            documents_analysis=json.dumps(documents_analysis, indent=2)
        )
        return await self.generate_text(prompt, max_tokens=8192)

    async def classify_document(self, image_base64: str, filename: str) -> Dict[str, Any]:
        """Classify a document using vision."""
        logger.info(f"Classifying document: {filename}")
        try:
            return await self.analyze_with_vision(
                images_base64=[image_base64],
                prompt=f"Classify this document. Filename: {filename}",
                system_prompt=get_system_prompt("document_classifier")
            )
        except Exception as e:
            logger.error(f"Error classifying {filename}: {e}")
            return {"document_type": "other", "confidence": 0.0, "error": str(e)}

    async def synthesize_documents(self, documents_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize results from multiple documents."""
        logger.info(f"Synthesizing {len(documents_results)} documents")
        try:
            response_text = await self.generate_text(
                get_prompt("synthesize_documents", documents_json=json.dumps(documents_results, indent=2)),
                system_prompt=get_system_prompt("synthesis")
            )
            return self._parse_json_response(response_text)
        except json.JSONDecodeError:
            return {
                "summary": "Documents processed. Detailed synthesis unavailable.",
                "total_annual_costs": 0,
                "total_one_time_costs": 0,
                "risk_level": "unknown",
                "key_findings": ["Processing completed"],
                "recommendations": ["Review individual documents"]
            }

    async def process_document_with_vision(
        self,
        images_base64: List[str],
        document_type: str,
        filename: str,
        subtype: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a document with vision capabilities."""
        logger.info(f"Processing {document_type}: {filename}")
        prompt_map = {
            "pv_ag": "process_pv_ag",
            "diagnostic": "process_diagnostic",
            "taxe_fonciere": "process_tax",
            "charges": "process_charges"
        }
        result = await self.analyze_with_vision(
            images_base64=images_base64,
            prompt=get_prompt(prompt_map.get(document_type, "process_diagnostic")),
            system_prompt=get_system_prompt("document_analyzer")
        )
        return {"parsed_data": result, "model": self.model}


# Singleton
_instance: Optional[DocumentAnalyzer] = None


def get_document_analyzer() -> DocumentAnalyzer:
    """Get or create the DocumentAnalyzer singleton."""
    global _instance
    if _instance is None:
        _instance = DocumentAnalyzer()
    return _instance


# Backward compatibility aliases
GeminiLLMService = DocumentAnalyzer
get_gemini_llm_service = get_document_analyzer
