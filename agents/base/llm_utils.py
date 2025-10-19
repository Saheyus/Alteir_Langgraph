#!/usr/bin/env python3
"""
Utilitaires LLM agnostiques du fournisseur
"""
from typing import Any, Type, TypeVar, Optional, List, Dict, Iterator, Union
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel
from pathlib import Path
from datetime import datetime
import json
import uuid

T = TypeVar('T', bound=BaseModel)

class LLMAdapter:
    """
    Adaptateur pour gérer différents fournisseurs LLM
    
    Supporte :
    - OpenAI (Structured Outputs natif)
    - Anthropic, Mistral, Ollama (JSON mode + parsing)
    - Fallback sur parsing manuel
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.provider = self._detect_provider()
        self.supports_structured = self._check_structured_support()
        self._raw_dir = Path("outputs") / "raw_llm"
        try:
            self._raw_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Ne pas faire échouer si le dossier ne peut pas être créé
            pass

    # ---------------------------------------------------------------------
    # Raw dump helpers
    # ---------------------------------------------------------------------
    def _get_model_name(self) -> str:
        try:
            # LangChain OpenAI exposes .model or .model_name depending on version
            model = getattr(self.llm, "model", None) or getattr(self.llm, "model_name", None)
            return str(model) if model else "unknown"
        except Exception:
            return "unknown"

    def _normalize_messages(self, messages: Any) -> Any:
        # Try to convert messages into a JSON-serializable structure
        try:
            if isinstance(messages, list):
                normalized: List[Dict[str, Any]] = []
                for m in messages:
                    if isinstance(m, dict):
                        role = m.get("role") or m.get("type") or "user"
                        content = m.get("content")
                        if not isinstance(content, (str, list, dict)):
                            content = str(content)
                        normalized.append({"role": str(role), "content": content})
                    else:
                        role = getattr(m, "role", "user")
                        content = getattr(m, "content", None)
                        if not isinstance(content, (str, list, dict)):
                            content = str(content)
                        normalized.append({"role": str(role), "content": content})
                return normalized
            # Fallback: stringify anything else
            return messages if isinstance(messages, (str, dict)) else str(messages)
        except Exception:
            return str(messages)

    def _serialize_response(self, response: Any) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "repr": None,
            "text": None,
            "content": None,
            "response_metadata": None,
            "type": type(response).__name__ if response is not None else None,
        }
        try:
            data["repr"] = repr(response)
        except Exception:
            pass
        try:
            data["text"] = self._extract_text(response)
        except Exception:
            data["text"] = None
        try:
            if hasattr(response, "content"):
                content = getattr(response, "content")
                if isinstance(content, (str, list, dict)):
                    data["content"] = content
                else:
                    data["content"] = str(content)
        except Exception:
            pass
        try:
            meta = getattr(response, "response_metadata", None)
            if meta is not None:
                # Ensure JSON-serializable
                if isinstance(meta, (dict, list, str, int, float, bool)):
                    data["response_metadata"] = meta
                else:
                    data["response_metadata"] = str(meta)
        except Exception:
            pass
        return data

    def _dump_raw(self, payload: Dict[str, Any]) -> Optional[Path]:
        try:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            base = f"{ts}_{self.provider}_{self._get_model_name()}_{uuid.uuid4().hex[:8]}.json"
            path = self._raw_dir / base
            # Avoid leaking API keys accidentally: scrub common keys
            def _scrub(d: Any) -> Any:
                if isinstance(d, dict):
                    return {k: ("***" if k.lower() in ("api_key", "authorization", "openai_api_key") else _scrub(v)) for k, v in d.items()}
                if isinstance(d, list):
                    return [_scrub(x) for x in d]
                return d
            with path.open("w", encoding="utf-8") as f:
                json.dump(_scrub(payload), f, ensure_ascii=False, indent=2)
            return path
        except Exception:
            return None

    def _save_raw_call(self, stage: str, messages: Any, response: Any = None, error: str | None = None, extra: Dict[str, Any] | None = None) -> None:
        payload: Dict[str, Any] = {
            "stage": stage,
            "provider": self.provider,
            "model": self._get_model_name(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "messages": self._normalize_messages(messages),
            "error": error,
        }
        if extra:
            payload["extra"] = extra
        if response is not None:
            payload["response"] = self._serialize_response(response)
        self._dump_raw(payload)

    # Public helpers for agents
    def invoke_text(self, messages: Any, label: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> str:
        """Invoke the underlying LLM and return extracted text, saving raw I/O to disk."""
        try:
            call_kwargs = {}
            # Forward Anthropic vendor kwargs if present (thinking, etc.)
            try:
                if hasattr(self.llm, "_alt_anthropic_kwargs"):
                    call_kwargs.update(getattr(self.llm, "_alt_anthropic_kwargs") or {})
            except Exception:
                pass
            # Pre-call diagnostic dump
            try:
                diag = {
                    "provider": self.provider,
                    "model": self._get_model_name(),
                    "call_kwargs": call_kwargs,
                    "has_alt_kwargs": hasattr(self.llm, "_alt_anthropic_kwargs"),
                    "alt_kwargs": getattr(self.llm, "_alt_anthropic_kwargs", None),
                    "temperature": getattr(self.llm, "temperature", None),
                }
                self._save_raw_call(stage=(label or "invoke") + ":pre", messages=messages, response=None, extra=diag)
            except Exception:
                pass
            response = self.llm.invoke(messages, **call_kwargs)
            # Save ASAP
            self._save_raw_call(stage=label or "invoke", messages=messages, response=response, extra=extra)
            return self._extract_text(response)
        except Exception as e:
            # Save error case as well
            self._save_raw_call(stage=(label or "invoke") + ":error", messages=messages, response=None, error=str(e), extra=extra)
            raise

    def save_final_text(self, messages: Any, text: str, label: str = "stream_complete", extra: Optional[Dict[str, Any]] = None) -> None:
        """Persist the final concatenated text of a streaming call."""
        payload = {
            "stage": label,
            "provider": self.provider,
            "model": self._get_model_name(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "messages": self._normalize_messages(messages),
            "response": {"text": text},
        }
        if extra:
            payload["extra"] = extra
        self._dump_raw(payload)
    
    def _detect_provider(self) -> str:
        """Détecte le fournisseur du LLM"""
        llm_type = type(self.llm).__name__.lower()
        
        if 'openai' in llm_type:
            return 'openai'
        elif 'anthropic' in llm_type or 'claude' in llm_type:
            return 'anthropic'
        elif 'mistral' in llm_type:
            return 'mistral'
        elif 'ollama' in llm_type:
            return 'ollama'
        else:
            return 'unknown'
    
    def _check_structured_support(self) -> bool:
        """Vérifie si le LLM supporte structured outputs natifs"""
        # Support explicite si l'objet expose with_structured_output
        if hasattr(self.llm, 'with_structured_output'):
            return True
        
        # Anthropic Claude 3+ supporte JSON mode (similaire)
        if self.provider == 'anthropic':
            return True
        
        return False
    
    def get_structured_output(
        self,
        prompt: Any,
        schema: Type[T],
        fallback_parser: Optional[callable] = None,
    ) -> T:
        """
        Obtient une sortie structurée du LLM
        
        Args:
            prompt: Prompt (str) ou messages (List[Dict]) à envoyer
            schema: Classe Pydantic définissant la structure
            fallback_parser: Parser de secours si structured outputs indisponible
            
        Returns:
            Instance de schema avec les données
        """
        # 1. Structured Outputs natifs (OpenAI, Anthropic)
        if self.supports_structured:
            try:
                # Prefer native structured outputs when available
                if hasattr(self.llm, 'with_structured_output'):
                    structured_llm = self.llm.with_structured_output(schema)
                    result = structured_llm.invoke(prompt)
                    # On ne dispose pas forcément de la réponse brute; loggons le prompt et le résultat structuré
                    self._save_raw_call(stage="structured.invoke", messages=prompt, response=None, extra={"structured_output": True, "schema": schema.__name__ if hasattr(schema, "__name__") else str(schema)})
                    return result

                elif self.provider == 'anthropic':
                    # Anthropic utilise tool_choice avec JSON schema
                    from langchain_core.utils.function_calling import convert_to_anthropic_tool
                    tool = convert_to_anthropic_tool(schema)
                    response = self.llm.invoke(
                        prompt,
                        tools=[tool],
                        tool_choice={"type": "tool", "name": tool["name"]}
                    )
                    # Save raw response
                    self._save_raw_call(stage="structured.anthropic.invoke", messages=prompt, response=response, extra={"schema": tool.get("name")})
                    return schema.model_validate(response.tool_calls[0]["args"])
            
            except Exception as e:
                print(f"[WARNING] Structured output failed: {e}, using fallback")
        
        # 2. JSON mode générique (Mistral, Ollama, etc.)
        try:
            # Ajouter instruction JSON au prompt
            # Autoriser les messages en entrée
            if isinstance(prompt, list):
                prompt_text = self._messages_to_text(prompt)
            else:
                prompt_text = str(prompt)

            json_prompt = f"""{prompt_text}

IMPORTANT: Réponds UNIQUEMENT avec un JSON valide suivant ce schéma:
{schema.model_json_schema()}

Ne pas ajouter de texte avant ou après le JSON."""

            response = self.llm.invoke(json_prompt)
            content = self._extract_text(response)
            # Save raw JSON-mode attempt
            self._save_raw_call(stage="json_mode.invoke", messages=json_prompt, response=response, extra={"schema": getattr(schema, "__name__", str(schema))})
            
            # Extraire JSON du texte
            import json
            import re
            
            # Chercher le JSON entre ```json ou directement
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Chercher le premier objet JSON valide
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                json_str = json_match.group(0) if json_match else content
            
            data = json.loads(json_str)
            return schema.model_validate(data)
        
        except Exception as e:
            print(f"[WARNING] JSON parsing failed: {e}")
        
        # 3. Fallback sur parser manuel
        if fallback_parser:
            try:
                # Si messages, les passer tels quels
                raw_response = self.llm.invoke(prompt)
                # Save fallback raw before parsing
                self._save_raw_call(stage="fallback.invoke", messages=prompt, response=raw_response)
                content = self._extract_text(raw_response)
                return fallback_parser(content, schema)
            except Exception as e:
                print(f"[ERROR] Fallback parser failed: {e}")
        
        # 4. Dernier recours : retour vide
        return schema()
    
    def stream_text(
        self,
        messages: Any,
        include_reasoning: bool = False,
    ) -> Iterator[Union[str, Dict[str, str]]]:
        """Stream textual output from the underlying LLM.
        
        Args:
            messages: Prompt or messages list (same format as invoke)
            include_reasoning: Try to surface reasoning stream when available
        Yields:
            Either plain text deltas (str) or dicts {"text", "reasoning"}
        """
        # Fallback: if streaming not supported, yield once with full text
        if not hasattr(self.llm, "stream"):
            try:
                response = self.llm.invoke(messages)
                text = self._extract_text(response)
                yield text
                return
            except Exception:
                return
        
        try:
            call_kwargs = {}
            try:
                if hasattr(self.llm, "_alt_anthropic_kwargs"):
                    call_kwargs.update(getattr(self.llm, "_alt_anthropic_kwargs") or {})
            except Exception:
                pass
            # Pre-stream diagnostic dump
            try:
                diag = {
                    "provider": self.provider,
                    "model": self._get_model_name(),
                    "call_kwargs": call_kwargs,
                    "has_alt_kwargs": hasattr(self.llm, "_alt_anthropic_kwargs"),
                    "alt_kwargs": getattr(self.llm, "_alt_anthropic_kwargs", None),
                    "temperature": getattr(self.llm, "temperature", None),
                }
                self._save_raw_call(stage="stream:pre", messages=messages, response=None, extra=diag)
            except Exception:
                pass
            stream = self.llm.stream(messages, **call_kwargs)
        except Exception as e:
            # If OpenAI Responses API refuses streaming (org not verified etc.), emulate streaming
            # by chunking a non-streaming response so the UI still gets live updates.
            try:
                response = self.llm.invoke(messages)
                full_text = self._extract_text(response)
                # Emit in small chunks to simulate token stream
                chunk_size = 80
                for i in range(0, len(full_text), chunk_size):
                    yield full_text[i : i + chunk_size]
            except Exception:
                pass
            return
        
        # Iterate chunks and extract incremental text (and optional reasoning)
        for chunk in stream:
            try:
                # LangChain AIMessageChunk usually exposes .content as a delta string
                delta_text: str = ""
                reasoning_delta: str = ""
                content = getattr(chunk, "content", None)
                if isinstance(content, str):
                    delta_text = content
                elif isinstance(content, list):
                    # Responses API may provide list of parts; collect text and reasoning
                    for part in content:
                        if isinstance(part, dict):
                            # Normalize part type; Responses API may use dotted types like "output_text.delta"
                            part_type_raw = part.get("type") or part.get("role")
                            base_type = None
                            if isinstance(part_type_raw, str):
                                base_type = part_type_raw.split(".")[0]
                            # Prefer explicit text field; some providers use "content"
                            maybe_text = None
                            txt = part.get("text")
                            if isinstance(txt, str):
                                maybe_text = txt
                            elif isinstance(part.get("content"), str):
                                maybe_text = part.get("content")
                            elif base_type == "thinking" and isinstance(part.get("thinking"), str):
                                # Anthropic extended thinking streams text under the 'thinking' key
                                if include_reasoning:
                                    reasoning_delta += part.get("thinking") or ""
                                # Do not treat as output text
                                maybe_text = None

                            if maybe_text is not None:
                                # Route reasoning separately; if not requested, ignore reasoning parts entirely
                                if base_type in ("reasoning", "thought", "chain_of_thought", "thinking"):
                                    if include_reasoning:
                                        reasoning_delta += maybe_text
                                    # else: ignore reasoning chunk to avoid polluting output text
                                else:
                                    delta_text += maybe_text
                            else:
                                # If no direct text fields, last-resort stringify known shapes
                                if base_type in ("reasoning", "thought", "chain_of_thought", "thinking"):
                                    if include_reasoning:
                                        # Avoid dumping raw dicts; try nested content
                                        nested_reason = part.get("thinking")
                                        if isinstance(nested_reason, str):
                                            reasoning_delta += nested_reason
                                        # else: skip unknown shapes silently
                                    # else ignore
                                else:
                                    # Avoid stalling: try to recover any displayable text
                                    # Common nested shapes: {type: ..., "output_text": {"content": "..."}}
                                    nested = part.get("output_text") or part.get("message") or part.get("delta")
                                    nested_text = None
                                    if isinstance(nested, dict):
                                        ct = nested.get("content") or nested.get("text")
                                        if isinstance(ct, str):
                                            nested_text = ct
                                    if isinstance(nested_text, str):
                                        delta_text += nested_text
                                    # else: skip unknown shapes to avoid dumping raw dicts
                        else:
                            # Unknown object; stringify
                            delta_text += str(part)
                else:
                    # Fallback to string extraction
                    text = self._extract_text(chunk)
                    delta_text = text
                
                if include_reasoning and reasoning_delta:
                    # Prefer emitting both fields when available; avoid empty text dicts
                    if delta_text:
                        yield {"text": delta_text, "reasoning": reasoning_delta}
                    else:
                        # If only reasoning arrives, still yield a dict, but keep text empty to not break consumers
                        yield {"text": "", "reasoning": reasoning_delta}
                else:
                    # Yield plain string for simplicity and backwards-compatibility
                    if delta_text:
                        yield delta_text
            except Exception:
                # Ignore malformed chunks and continue
                continue
    
    def _extract_text(self, response: Any) -> str:
        """Extrait le texte d'une réponse LLM"""
        if isinstance(response, str):
            return self._sanitize_provider_artifacts(response)
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, str):
                return self._sanitize_provider_artifacts(content)
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict) and 'text' in p:
                        parts.append(p['text'])
                    elif hasattr(p, 'text'):
                        parts.append(p.text)
                    else:
                        parts.append(str(p))
                return self._sanitize_provider_artifacts(''.join(parts))
        return self._sanitize_provider_artifacts(str(response))

    def _sanitize_provider_artifacts(self, text: str) -> str:
        """Nettoie les artefacts connus provenant de certains streams fournisseurs.

        Exemples: "{'index': 1}" collé à la fin d'une ligne, ou variantes similaires.
        Ne modifie pas le contenu sémantique attendu.
        """
        try:
            import re
            # Pattern 1: artefact isolé en fin de ligne ou après un token
            text = re.sub(r"\{\'index\':\s*\d+\}\s*", "", text)
            text = re.sub(r"\{\"index\":\s*\d+\}\s*", "", text)
            # Pattern 2: mêmes artefacts précédés d'un espace ou collés
            text = re.sub(r"\s*\{index:\s*\d+\}\s*", "", text)
            # Collapse accidental double spaces left by removals
            text = re.sub(r"[ \t]{2,}", " ", text)
            return text
        except Exception:
            return text

    def _messages_to_text(self, messages: List[Dict[str, Any]]) -> str:
        """Convertit une liste de messages {role, content} en texte concaténé pour JSON-mode."""
        parts: List[str] = []
        for m in messages:
            role = m.get('role', 'user')
            content = m.get('content', '')
            parts.append(f"[{role.upper()}]\n{content}")
        return "\n\n".join(parts)


# Exemple d'utilisation
def example_usage():
    """Exemple d'utilisation de LLMAdapter"""
    from pydantic import BaseModel, Field
    from typing import List
    
    # Définir le schéma
    class Correction(BaseModel):
        type: str = Field(description="Type de correction (orthographe, grammaire, etc.)")
        original: str = Field(description="Texte original")
        corrected: str = Field(description="Texte corrigé")
        explanation: str = Field(description="Explication de la correction")
    
    class CorrectionResult(BaseModel):
        corrections: List[Correction]
        summary: str
    
    # Parser de fallback manuel (optionnel)
    def manual_parser(text: str, schema: Type[BaseModel]) -> BaseModel:
        """Parser manuel si tout échoue"""
        # Logique de parsing custom
        corrections = []
        for line in text.split('\n'):
            if '[CORRECTION:' in line:
                # Extraire les infos...
                pass
        return schema(corrections=corrections, summary="")
    
    # Utilisation avec n'importe quel LLM
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-5-nano")  # Ou Anthropic, Mistral, etc.
    adapter = LLMAdapter(llm)
    
    prompt = "Corrige ce texte: 'Je vais au marché demain matin.'"
    
    result = adapter.get_structured_output(
        prompt=prompt,
        schema=CorrectionResult,
        fallback_parser=manual_parser
    )
    
    # result est typé et structuré !
    for corr in result.corrections:
        print(f"{corr.type}: {corr.original} -> {corr.corrected}")

if __name__ == "__main__":
    example_usage()

