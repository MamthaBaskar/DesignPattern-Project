"""
AI Client module with multi-provider support (OpenAI, Gemini, Anthropic)
and graceful deterministic semantic fallbacks.
"""

import json
import logging
import re
from typing import Any, Dict, Optional
import httpx

from .config import AIConfig
from .prompts import SYSTEM_COMPARISON_PROMPT, build_analysis_user_prompt
from ..comparison.classifier import classify_change
from ..models.schemas import ChangeCategory, ChangeType, ConfidenceLevel, ImportanceLevel

logger = logging.getLogger(__name__)


class AIClient:
    """
    Robust AI client executing Prompt Chaining analysis with graceful fallback.
    """

    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()

    def _call_openai_compatible(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes OpenAI or OpenAI-compatible endpoint."""
        url = f"{self.config.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_COMPARISON_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            with httpx.Client(timeout=self.config.REQUEST_TIMEOUT) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                else:
                    logger.warning(f"OpenAI call returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")

        return None

    def _call_gemini(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Google Gemini REST API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.GEMINI_MODEL}:generateContent?key={self.config.GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_COMPARISON_PROMPT}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        try:
            with httpx.Client(timeout=self.config.REQUEST_TIMEOUT) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
                else:
                    logger.warning(f"Gemini call returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")

        return None

    def analyze_change_prompt_chain(
        self,
        change_type: ChangeType,
        old_text: str,
        new_text: str,
        section: str,
        rag_context: str,
    ) -> Dict[str, Any]:
        """
        Executes Prompt Chaining analysis.
        If credentials missing or API fails, uses deterministic semantic classifier.
        """
        # Step 1: Try configured LLM API if key is present
        if self.config.is_ai_configured():
            user_prompt = build_analysis_user_prompt(
                old_text=old_text,
                new_text=new_text,
                change_type=change_type.value,
                section=section,
                rag_context=rag_context,
            )

            result: Optional[Dict[str, Any]] = None
            if self.config.PROVIDER in ("openai", "custom") and self.config.OPENAI_API_KEY:
                result = self._call_openai_compatible(user_prompt)
            elif self.config.PROVIDER == "gemini" and self.config.GEMINI_API_KEY:
                result = self._call_gemini(user_prompt)

            if result and "category" in result and "importance" in result:
                # Validate enum values
                category_val = result.get("category", ChangeCategory.OTHER.value)
                importance_val = result.get("importance", ImportanceLevel.LOW.value)

                # Ensure category matches schema enum
                valid_categories = {c.value: c for c in ChangeCategory}
                matched_category = valid_categories.get(category_val, ChangeCategory.OTHER)

                valid_importances = {i.value: i for i in ImportanceLevel}
                matched_importance = valid_importances.get(importance_val, ImportanceLevel.LOW)

                valid_confidences = {c.value: c for c in ConfidenceLevel}
                matched_confidence = valid_confidences.get(result.get("confidence", "HIGH"), ConfidenceLevel.HIGH)

                return {
                    "category": matched_category,
                    "importance": matched_importance,
                    "impact": result.get("impact", ""),
                    "explanation": result.get("explanation", ""),
                    "confidence": matched_confidence,
                    "is_meaningful": result.get("reasoning_stage_2_meaning_changed", True),
                    "ai_applied": True,
                }

        # Step 2: Fallback deterministic semantic comparison
        # Cleanly performs the Prompt Chaining logic with local deterministic rules
        category, importance, impact, explanation, confidence, is_meaningful = classify_change(
            change_type=change_type,
            old_text=old_text,
            new_text=new_text,
        )

        return {
            "category": category,
            "importance": importance,
            "impact": impact,
            "explanation": explanation,
            "confidence": confidence,
            "is_meaningful": is_meaningful,
            "ai_applied": False,
        }

