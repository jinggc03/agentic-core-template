"""Anti-loop protection for agent execution.

Detects and stops:
- Same input repeated consecutively
- Same tool called too many times in a row
- Turns looping without progress
- Execution timeout (via asyncio.wait_for at runner level)

Usage:
    guard = LoopGuard()
    guard.check_input(user_input)         # raises LoopDetectedError if looping
    guard.check_tool_call(tool_name)      # raises LoopDetectedError if same tool spammed
    guard.check_output(output)            # raises LoopDetectedError if same output repeated
    guard.on_turn_complete(user_input, output)  # call at end of each turn
"""

from typing import Optional
from collections import Counter
from app.core.logging import get_logger

logger = get_logger(__name__)


class LoopDetectedError(RuntimeError):
    """Raised when a loop pattern is detected in agent execution."""
    pass


class LoopGuard:
    """Stateful guard that detects repetitive patterns across turns.

    One instance should be created per agent conversation.
    """

    def __init__(
        self,
        max_repeated_input: int = 3,
        max_same_tool_consecutive: int = 5,
        max_repeated_output: int = 3,
    ):
        """Initialize guard.

        Args:
            max_repeated_input: How many identical consecutive inputs trigger an error
            max_same_tool_consecutive: How many times the same tool can be called in a row
            max_repeated_output: How many identical consecutive outputs trigger an error
        """
        self.max_repeated_input = max_repeated_input
        self.max_same_tool_consecutive = max_same_tool_consecutive
        self.max_repeated_output = max_repeated_output

        self._last_input: Optional[str] = None
        self._input_repeat_count: int = 0

        self._last_tool: Optional[str] = None
        self._tool_consecutive_count: int = 0

        self._last_output: Optional[str] = None
        self._output_repeat_count: int = 0

    # ── Input check ──────────────────────────────────────────────────────────

    def check_input(self, user_input: str) -> None:
        """Check for repeated identical inputs.

        Args:
            user_input: The current user input

        Raises:
            LoopDetectedError: If same input repeated too many times
        """
        normalized = user_input.strip().lower()
        if normalized == self._last_input:
            self._input_repeat_count += 1
            if self._input_repeat_count >= self.max_repeated_input:
                logger.warning(
                    f"LoopGuard: same input repeated {self._input_repeat_count} times"
                )
                raise LoopDetectedError(
                    f"Same input repeated {self._input_repeat_count} times — "
                    "possible loop detected. Stopping execution."
                )
        else:
            self._last_input = normalized
            self._input_repeat_count = 1

    # ── Tool call check ───────────────────────────────────────────────────────

    def check_tool_call(self, tool_name: str) -> None:
        """Check for same tool being called consecutively too many times.

        Args:
            tool_name: Name of the tool about to be called

        Raises:
            LoopDetectedError: If same tool called too many times consecutively
        """
        if tool_name == self._last_tool:
            self._tool_consecutive_count += 1
            if self._tool_consecutive_count >= self.max_same_tool_consecutive:
                logger.warning(
                    f"LoopGuard: tool '{tool_name}' called "
                    f"{self._tool_consecutive_count} times consecutively"
                )
                raise LoopDetectedError(
                    f"Tool '{tool_name}' called {self._tool_consecutive_count} "
                    "times consecutively — possible tool loop. Stopping execution."
                )
        else:
            self._last_tool = tool_name
            self._tool_consecutive_count = 1

    # ── Output check ──────────────────────────────────────────────────────────

    def check_output(self, output: str) -> None:
        """Check for repeated identical outputs.

        Args:
            output: The agent output to check

        Raises:
            LoopDetectedError: If same output repeated too many times
        """
        normalized = output.strip()
        if normalized == self._last_output:
            self._output_repeat_count += 1
            if self._output_repeat_count >= self.max_repeated_output:
                logger.warning(
                    f"LoopGuard: same output repeated {self._output_repeat_count} times"
                )
                raise LoopDetectedError(
                    f"Same output repeated {self._output_repeat_count} times — "
                    "agent appears stuck in a loop. Stopping execution."
                )
        else:
            self._last_output = normalized
            self._output_repeat_count = 1

    # ── Convenience ──────────────────────────────────────────────────────────

    def on_turn_complete(self, user_input: str, output: str) -> None:
        """Record a completed turn (call at end of each turn for tracking).

        Does NOT raise — use check_input/check_output *before* execution.
        This just logs for observability.
        """
        logger.debug(
            f"LoopGuard state: input_repeats={self._input_repeat_count}, "
            f"output_repeats={self._output_repeat_count}, "
            f"last_tool_count={self._tool_consecutive_count}"
        )

    def reset(self) -> None:
        """Reset all counters (e.g., after agent.reset())."""
        self._last_input = None
        self._input_repeat_count = 0
        self._last_tool = None
        self._tool_consecutive_count = 0
        self._last_output = None
        self._output_repeat_count = 0
