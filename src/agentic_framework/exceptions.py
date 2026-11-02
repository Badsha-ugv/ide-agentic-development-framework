"""Framework-specific exceptions."""


class AgenticFrameworkError(Exception):
    """Base class for expected framework errors."""


class ConfigurationError(AgenticFrameworkError):
    """Raised when configuration cannot be read or validated."""


class InitializationError(AgenticFrameworkError):
    """Raised when a target project cannot be initialized safely."""


class RequirementsError(AgenticFrameworkError):
    """Raised when requirements cannot be versioned safely."""


class StateError(AgenticFrameworkError):
    """Raised when persistent runtime state is invalid or a transition is unsafe."""

