import time


def countdown(seconds: int) -> None:
    while seconds > 0:
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)

        countdown_str = "{:02d}:{:02d}:{:02d}:{:02d}".format(days, hours, mins, secs)
        print(countdown_str, "Until Surena stops.", end="\r")

        time.sleep(1)
        seconds -= 1
