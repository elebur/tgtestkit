class TgTestKitBaseError(Exception):
    """The base exception of the package."""


class ExpectationError(TgTestKitBaseError):
    """Raised when peer's response did not match the `Expectation`."""
