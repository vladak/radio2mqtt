"""
generic binary state tracking class

modified from the vladak/workmon/binarystate.py to track the time in milliseconds
"""

import time

import adafruit_logging as logging


class BinaryState:
    """
    provides state tracking based on updating value periodically
    The state duration is stored as float in order to allow for sub-second updates.
    This in turn can lead to lose of precision over time.
    """

    def __init__(
        self,
    ):
        """
        set the initial state
        """
        self.cur_state = None  # opaque current state
        self.state_duration = 0  # duration of current state in milliseconds
        self.stamp = time.monotonic_ns()  # use _ns() to avoid losing precision

    def update(self, cur_state) -> float:
        """
        :param cur_state: current state
        :return: duration of the state in milliseconds
        """
        logger = logging.getLogger(__name__)

        # Record the duration.
        if self.cur_state is not None:
            if self.cur_state == cur_state:
                self.state_duration += (time.monotonic_ns() - self.stamp) // 1_000_000
                logger.debug(
                    f"state '{cur_state}' preserved (for {self.state_duration} msec)"
                )
            else:
                logger.debug(f"state changed {self.cur_state} -> {cur_state}")
                self.state_duration = 0

        self.cur_state = cur_state
        self.stamp = time.monotonic_ns()

        return self.state_duration

    def reset(self):
        """
        reset the state
        """
        self.cur_state = None
        self.state_duration = 0
