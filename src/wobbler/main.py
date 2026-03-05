""" @file main.py
    @author Sean Duffie
    @brief Main file for the wobbler.

The Wobbler was initially supposed to use the mouse package to wobble the mouse every certain
interval in minutes, and give the user an option to input a different value. However, I
learned that for some reason the scripted mouse movements don't reset the Windows sleep timer.

An alternative solution a found and implemented was setting the Windows ThreadExecutionState.
This can be done using the ctypes library and the commands:
    - ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)  # lock
    - ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # unlock
The documentation for this can be found at:
    - https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
This is preferable to the original method because it doesn't require threads and it doesn't
interfere with standard user operation.

"""

import ctypes
from loguru import logger
import sys
import threading
import time

# import mouse

# Windows API Constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# Virtual Key code for F15 (registers as activity, but rarely affects applications)
VK_F15 = 0x7E
KEYEVENTF_KEYUP = 0x0002


def setup_logging():
    # Remove the default handler (so you can configure your own)
    logger.remove()

    # Add a console handler (for you to see)
    logger.add(sys.stderr, level="INFO")

    # Add a file handler (for history)
    # "rotation" creates a new file every 10MB or every day
    # "retention" keeps logs for 10 days before deleting old ones
    logger.add("logs/app.log", rotation="10 MB", retention="10 days", level="DEBUG")


def press_f15():
    """Simulates a hardware-level F15 key press and release using ctypes."""
    ctypes.windll.user32.keybd_event(VK_F15, 0, 0, 0)  # Press
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_F15, 0, KEYEVENTF_KEYUP, 0)  # Release


class Wobbler:
    def __init__(self, interval: int = 1):
        self.interval_minutes = 1
        self.stop_event = threading.Event()

    def set_execution_state(self, enable: bool):
        """Toggles the Windows ThreadExecutionState."""
        if enable:
            state = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            ctypes.windll.kernel32.SetThreadExecutionState(state)
            logger.debug("Execution state lock requested.")
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            logger.debug("Execution state unlocked.")

    def wobble_loop(self):
        """Background loop that presses F15 at the given interval."""
        self.set_execution_state(True)

        while not self.stop_event.is_set():
            logger.info("Sending activity signal (F15)...")
            press_f15()

            # mouse.move(50, 50, absolute=False, duration=0.1)
            # # mouse.move(-100,-100, absolute=False, duration=0.1)
            # mouse.move(-50, -50, absolute=False, duration=0.1)

            # Wait in 1-second increments for a highly responsive shutdown
            for _ in range(self.interval_minutes * 60):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def start(self):
        setup_logging()
        logger.info(
            f"WOBBLER LAUNCHED AT {self.interval_minutes} MINUTES"
        )  # Daemon thread ensures it dies if the main thread crashes
        wobble_thread = threading.Thread(target=self.wobble_loop, daemon=True)
        wobble_thread.start()

        # Main thread handles user input and graceful shutdown via KeyboardInterrupt
        try:
            while True:
                user_input = input(
                    f"Current interval: {self.interval_minutes}m. Enter new interval (or CTRL+C to quit):\n"
                )
                try:
                    new_interval = int(user_input)
                    if new_interval > 0:
                        self.interval_minutes = new_interval
                        logger.info(
                            f"Interval updated to {self.interval_minutes} minutes."
                        )
                    else:
                        logger.error("Must be a positive integer. Try again.")
                except ValueError:
                    logger.error("Not an integer! Try again.")

        except KeyboardInterrupt:
            logger.info("User manually initiated shutdown using CTRL+C...")

        finally:
            self.stop_event.set()  # Signal the background thread to stop
            self.set_execution_state(False)  # Release the Windows lock
            wobble_thread.join()  # Wait for thread to finish cleanly
            logger.info("Shutdown complete.")


if __name__ == "__main__":
    sys.exit(Wobbler().start())
