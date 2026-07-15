from smolagents.models import Model, ChatMessage, MessageRole
from llama_cpp import Llama
from typing import Optional, List, Dict

class LocalGGUFModel(Model):
    """
    A custom Model wrapper for smolagents to natively use a local GGUF model via llama-cpp-python.
    """
    def __init__(self, model_path: str, n_ctx: int = 4096, **kwargs):
        super().__init__()
        self.model_path = model_path
        self.model = Llama(model_path=model_path, n_ctx=n_ctx, verbose=False, **kwargs)
        
    def generate(
        self,
        messages: List[ChatMessage],
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> ChatMessage:
        """Process messages and return the model's response."""
        formatted_messages = []
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            content = str(msg.content[0].text if isinstance(msg.content, list) else msg.content)
            formatted_messages.append({"role": role, "content": content})
            
        response = self.model.create_chat_completion(
            messages=formatted_messages,
            stop=stop_sequences or [],
            **kwargs
        )
        
        reply_text = response['choices'][0]['message']['content']
        return ChatMessage(role=MessageRole.ASSISTANT, content=reply_text)
