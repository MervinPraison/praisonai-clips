"""Failures shared by transports and editor clients."""


class ResolveError(RuntimeError):
    """A native operation failed; it may have performed earlier statements."""


class ResolveTransportError(ResolveError):
    """The result is unknown. Inspect the editor before retrying a mutation."""
