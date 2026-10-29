import re
import json
from dataclasses import dataclass

import httpx

from .core.config import Settings


@dataclass
class AnalysisResult:
    seller_name: str | None
    brand: str | None
    model_name: str | None
    size: str | None
    price: float | None
    city: str | None
    availability: str
    confidence: float
    signals: list[dict[str, str | float]]


class AiAnalyzer:
    """OpenAI Responses adapter with a deterministic local fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    def _openai_result(self, text: str) -> AnalysisResult | None:
        if not self.settings or not self.settings.openai_api_key:
            return None
        schema = {
            "type": "object",
            "properties": {
                "brand": {"type": ["string", "null"]}, "model_name": {"type": ["string", "null"]},
                "size": {"type": ["string", "null"]}, "price": {"type": ["number", "null"]},
                "city": {"type": ["string", "null"]}, "availability": {"type": "string"},
                "confidence": {"type": "number"}, "signals": {"type": "array", "items": {"type": "object", "properties": {"kind": {"type": "string"}, "intensity": {"type": "string"}, "confidence": {"type": "number"}}, "required": ["kind", "intensity", "confidence"], "additionalProperties": False}},
            },
            "required": ["brand", "model_name", "size", "price", "city", "availability", "confidence", "signals"],
            "additionalProperties": False,
        }
        body = {"model": self.settings.openai_model, "input": [{"role": "system", "content": [{"type": "input_text", "text": "Analiza publicaciones de tenis. Extrae datos de mercado en JSON; no inventes valores y usa null cuando falte información."}]}, {"role": "user", "content": [{"type": "input_text", "text": text}]}], "temperature": 0, "text": {"format": {"type": "json_schema", "name": "market_observation", "schema": schema, "strict": True}}}
        try:
            response = httpx.post("https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json"}, json=body, timeout=20)
            response.raise_for_status()
            payload = response.json()
            output_text = payload.get("output_text")
            if not output_text:
                return None
            result = json.loads(output_text)
            return AnalysisResult(seller_name=None, brand=result.get("brand"), model_name=result.get("model_name"), size=result.get("size"), price=result.get("price"), city=result.get("city"), availability=result.get("availability", "unknown"), confidence=float(result.get("confidence", 0.5)), signals=result.get("signals", []))
        except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def extract_product_data(self, text: str) -> AnalysisResult:
        remote = self._openai_result(text)
        if remote:
            return remote
        lower = text.lower()
        price_match = re.search(r"(?:bs\.?|bob|precio)\s*([0-9]{2,5})", lower)
        if not price_match:
            price_match = re.search(r"(?<!talla\s)(?<!size\s)(?<!\d)([1-9][0-9]{2,4})(?!\d)", lower)
        size_match = re.search(r"(?:talla|talle|size)\s*([0-9]{2}(?:\.5)?)", lower)
        brands = ["nike", "adidas", "jordan", "under armour", "puma", "anta", "new balance"]
        brand = next((item.title() for item in brands if item in lower), None)
        sold = any(item in lower for item in ("vendido", "ya se fue", "no disponible", "gracias por la compra"))
        interest = any(item in lower for item in ("me interesa", "talla 42", "cuánto", "precio", "disponible"))
        signals: list[dict[str, str | float]] = []
        if sold:
            signals.append({"kind": "sale", "intensity": "high", "confidence": 0.88})
        if interest:
            signals.append({"kind": "demand", "intensity": "medium", "confidence": 0.74})
        return AnalysisResult(
            seller_name=None,
            brand=brand,
            model_name=None,
            size=size_match.group(1) if size_match else None,
            price=float(price_match.group(1)) if price_match else None,
            city=None,
            availability="sold" if sold else "available" if price_match else "unknown",
            confidence=0.72 if price_match or brand else 0.35,
            signals=signals,
        )

