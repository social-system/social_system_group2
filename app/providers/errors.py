class ProviderError(Exception):
    """Base class for provider-specific internal errors."""


class ProviderConfigurationError(ProviderError):
    """Raised when a real provider execution path is not configured."""


class ProviderExecutionError(ProviderError):
    """Raised when a provider call fails during execution."""


class ProviderInvalidResponseError(ProviderError):
    """Raised when provider output cannot be normalized or validated."""
