from typing import Dict, List, Optional
from app.services.providers.base_provider import BaseProvider
from app.services.provider_factory import ProviderFactory

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        
    def register_provider(self, name: str, config: dict):
        try:
            provider = ProviderFactory.create(name, config)
            self._providers[name] = provider
        except Exception as e:
            # We catch it so we don't break the whole router if one provider fails to initialize
            import logging
            logging.getLogger("ProviderRegistry").error(f"Failed to register provider {name}: {e}")

    def unregister_provider(self, name: str):
        if name in self._providers:
            del self._providers[name]

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

# Singleton instance
provider_registry = ProviderRegistry()
