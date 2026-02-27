""" wobbler.py

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
import logging
import signal
import sys
import threading
import time

import mouse

INTERVAL = 4
END = False

def handler(signum, frame) -> None:
    """This function will handle any system interrupts that we decide to use
    It relies on the "signal" python library (see documentation below)
    https://docs.python.org/3/library/signal.html

    TODO: Add more handling so that the errors can return more information

    Args:
        signum (int): number associated with interrupt
        frame (frame): location that the interrupt came from
        signame (str): reads the name of the interrupt to the user
    Returns:
        None
    """
    signame = signal.Signals(signum).name

    if signame == "SIGINT":
        logging.info("User manually initiated shutdown using \"CTRL+C\"...")

        global END
        END = True

        # set back to normal
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

def interval_thread():
    """ Thread that runs alongside wobbler to handle user interactions """
    while not END:
        print("Enter in terminal the amount of minutes between wobbles: ")
        try:
            entry = int(input())
        except ValueError:
            logging.error("Not an int!")
            entry = -1
        if entry <= 0:
            logging.error("Must be a positive integer. Try again")
        else:
            global INTERVAL
            INTERVAL = entry

def wobble_thread():
    """ This operates on it's own timer to wobble the mouse by 50 pixels on a given interval """
    while not END:
        logging.info("INITIATING WOBBLE")
        # mouse.move(50, 50, absolute=False, duration=0.1)
        # # mouse.move(-100,-100, absolute=False, duration=0.1)
        # mouse.move(-50, -50, absolute=False, duration=0.1)

        # Delays for [INTERVAL] amount of minutes, [INTERVAL] seconds per sleep
        # Having more delays for shorter times each makes a more responsive UI
        c = 0
        while not END and c < 60:
            time.sleep(INTERVAL)
            c += 1

def main():
    # Initial Logger Settings
    fmt_main = "%(asctime)s\t| %(levelname)s\t| %(message)s"
    logging.basicConfig(format=fmt_main, level=logging.INFO,
                datefmt="%Y-%m-%d %H:%M:%S")

    # Initialize Listener (for CTRL+C interrupts)
    signal.signal(signal.SIGINT, handler)

    # prevent
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)

    # Break out into threads
    t1 = threading.Thread(target=wobble_thread)
    t1.start()
    logging.info("WOBBLER LAUNCHED AT %d MINUTES", INTERVAL)
    interval_thread()
    t1.join()


if __name__ == "__main__":
    sys.exit(main())
