#!/usr/bin/env python3
"""
Utilitaires LLM agnostiques du fournisseur
"""
from typing import Any, Type, TypeVar, Optional, List, Dict, Iterator, Union
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel

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
                    return structured_llm.invoke(prompt)

                elif self.provider == 'anthropic':
                    # Anthropic utilise tool_choice avec JSON schema
                    from langchain_core.utils.function_calling import convert_to_anthropic_tool
                    tool = convert_to_anthropic_tool(schema)
                    response = self.llm.invoke(
                        prompt,
                        tools=[tool],
                        tool_choice={"type": "tool", "name": tool["name"]}
                    )
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
            stream = self.llm.stream(messages)
        except Exception:
            # Fallback to non-streaming
            try:
                response = self.llm.invoke(messages)
                text = self._extract_text(response)
                yield text
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
                            part_type = part.get("type") or part.get("role")
                            # Prefer text, but some providers include content instead
                            maybe_text = part.get("text") if isinstance(part.get("text"), str) else None
                            if maybe_text is None and isinstance(part.get("content"), str):
                                maybe_text = part.get("content")

                            if maybe_text:
                                if part_type in ("output_text", "message", "text", None):
                                    delta_text += maybe_text
                                elif include_reasoning and part_type in ("reasoning", "thought", "chain_of_thought"):
                                    reasoning_delta += maybe_text
                            elif include_reasoning and part_type in ("reasoning", "thought"):
                                # Unknown structure: stringify as last resort
                                reasoning_delta += str(part)
                        else:
                            # Unknown object; stringify
                            delta_text += str(part)
                else:
                    # Fallback to string extraction
                    text = self._extract_text(chunk)
                    delta_text = text
                
                if include_reasoning and reasoning_delta:
                    yield {"text": delta_text, "reasoning": reasoning_delta}
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
            return response
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict) and 'text' in p:
                        parts.append(p['text'])
                    elif hasattr(p, 'text'):
                        parts.append(p.text)
                    else:
                        parts.append(str(p))
                return ''.join(parts)
        return str(response)

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

