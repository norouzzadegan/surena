import time


def countdown(secends: int) -> None:
    while secends:
        mins, secs = divmod(secends, 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)
        print(
            "{:02d}:{:02d}:{:02d}:{:02d}".format(days, hours, mins, secs),
            "Until to stop.",
            end="\r",
        )
        time.sleep(1)
        secends -= 1
