class LLMProvider:
    def __init__(self, provider: str):
        self.provider = provider

    def get_response(self, prompt: str):
        if self.provider == "openai":
            return self._openai_response(prompt)
        elif self.provider == "poe":
            return self._poe_response(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _openai_response(self, prompt: str):
        # This is a placeholder for the OpenAI API call
        return f"OpenAI response for prompt: {prompt}"

    def _poe_response(self, prompt: str):
        # This is a placeholder for the Poe API call
        return f"Poe response for prompt: {prompt}"