from dataclasses import dataclass


@dataclass
class TimeoutSettings:
    """
    Timeout settings for gathering messages.

    Attributes:
        max_wait (float): The maximum duration in seconds to wait for
            a response from the peer. Defaults to 10.
        wait_consecutive (float, optional): The minimum duration in seconds to wait
            for another consecutive message from the peer after receiving a message.
            This can cause the total duration to exceed the `max_wait` time.
        raise_on_timeout (bool): Whether to raise an exception when a timeout occurs
            or to fail with a log message. Defaults to False
    """

    max_wait: float = 10

    wait_consecutive: float | None = None

    raise_on_timeout: bool = False
