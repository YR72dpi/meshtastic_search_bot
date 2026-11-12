import logging
from typing import List, Optional

from tool.llm_providers.ollama import call_ollama
from tool.llm_providers.vireonix import call_vireonix

logger = logging.getLogger(__name__)


def _normalize_text(value: object) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text.lower() in {"none", "null", "n/a", "na"}:
        return None
    return text


def _provider_order(prefer: Optional[str] = None) -> List[str]:
    providers: List[str] = []
    if prefer:
        providers.append(prefer)
    for provider in ("vireonix", "ollama"):
        if provider not in providers:
            providers.append(provider)
    return providers


def call_llm(prompt: str, prefer: Optional[str] = "vireonix") -> str:
    """Appelle le fournisseur LLM disponible avec bascule Vireonix -> Ollama."""
    last_error: Optional[Exception] = None

    for provider in _provider_order(prefer=prefer):
        try:
            if provider == "vireonix":
                text = call_vireonix(prompt)
            elif provider == "ollama":
                text = call_ollama(prompt)
            else:
                raise ValueError(f"Fournisseur inconnu: {provider}")

            normalized = _normalize_text(text)
            if normalized is None:
                raise ValueError(f"Réponse vide depuis {provider}")
            return normalized
        except Exception as exc:
            last_error = exc
            logger.warning("[LLM] provider=%s failed: %s", provider, exc)

    if last_error is not None:
        raise RuntimeError(f"Tous les fournisseurs LLM ont échoué. Dernier échec: {last_error}")
    raise RuntimeError("Aucun fournisseur LLM disponible")


__all__ = ["call_llm", "call_vireonix", "call_ollama"]
