"""LLM Service for Huawei Cloud MaaS integration.

MaaS provides an OpenAI-compatible API, so we use the openai library
with custom base URL and API key.
"""

from openai import OpenAI
from app.config import load_config
from typing import List, Dict, Optional


class LLMService:
    """Service for interacting with Huawei Cloud MaaS LLM."""

    def __init__(self):
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """Get or create the OpenAI client configured for MaaS."""
        config = load_config()

        if not config.maas.url or not config.maas.api_key:
            raise ValueError(
                "MaaS no está configurado. Por favor configure la URL, API Key y Modelo "
                "en la sección de configuración."
            )

        # Ensure URL ends with /v1 for OpenAI compatibility
        base_url = config.maas.url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"

        return OpenAI(
            api_key=config.maas.api_key,
            base_url=base_url
        )

    def generate_response(
        self,
        query: str,
        context_documents: List[str]
    ) -> str:
        """Generate a response using RAG (Retrieval-Augmented Generation).

        Args:
            query: The user's question.
            context_documents: Retrieved documents from ChromaDB to use as context.

        Returns:
            The generated response from the LLM.
        """
        config = load_config()

        if not config.maas.url or not config.maas.api_key or not config.maas.model:
            return (
                "⚠️ MaaS no está configurado. Por favor configure la URL, API Key y Modelo "
                "haciendo clic en el botón de configuración (⚙️) en la esquina superior derecha."
            )

        client = self._get_client()

        # Build the system prompt with context
        if context_documents:
            context_text = "\n\n---\n\n".join(context_documents)
            system_prompt = (
                "Eres un asistente útil y preciso. Responde las preguntas del usuario "
                "basándote EXCLUSIVAMENTE en la siguiente información proporcionada. "
                "Si la información proporcionada no es suficiente para responder la pregunta, "
                "indica claramente que no hay suficiente información disponible.\n\n"
                f"Información disponible:\n{context_text}"
            )
        else:
            system_prompt = (
                "Eres un asistente útil y preciso. No hay información disponible en la base "
                "de datos para responder la pregunta del usuario. Indica amablemente que "
                "no hay información en ChromaDB para responder su consulta."
            )

        try:
            response = client.chat.completions.create(
                model=config.maas.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Error al comunicarse con MaaS: {str(e)}"

    def test_connection(self) -> Dict[str, any]:
        """Test the connection to MaaS.

        Returns:
            Dict with success status and message.
        """
        config = load_config()

        if not config.maas.url or not config.maas.api_key or not config.maas.model:
            return {
                "success": False,
                "message": "MaaS no está completamente configurado."
            }

        try:
            client = self._get_client()
            # Try a simple completion to test the connection
            response = client.chat.completions.create(
                model=config.maas.model,
                messages=[
                    {"role": "user", "content": "Hola, responde con 'OK' si estás funcionando."}
                ],
                temperature=0,
                max_tokens=10
            )
            return {
                "success": True,
                "message": f"Conexión exitosa. Respuesta: {response.choices[0].message.content}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error de conexión: {str(e)}"
            }


# Singleton instance
llm_service = LLMService()
