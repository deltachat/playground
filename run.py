from __future__ import print_function

import threading
import random
import queue
import time


FOREGROUND = True


def log(*args):
    t = threading.current_thread()
    print(t, *args)


class ImapThread(threading.Thread):
    def run(self):
        while 1:
            perform_imap_jobs()
            if FOREGROUND:
                log("calling imap-idle")
                time.sleep(10)
            else:
                log("calling imap-poll (non-blocking)")
                break



def perform_imap_jobs():
    while 1:
        log("perform_imap_jobs: attempting to get a job")
        try:
            x = imap_queue.get(timeout=0.1)
        except queue.Empty:
            break
        else:
            log("processing imap job:", x)
    log("perform_imap_jobs: finished loop")



def on_receive():
    if not imap_thread.is_alive():
        log("no imap thread active: starting one")
        start_imap_thread()
    else:
        log("imap thread is already active, doing nothing")


imap_queue = queue.Queue()
imap_thread = None

def start_imap_thread():
    global imap_thread
    if imap_thread is not None and imap_thread.is_alive():
        log("skipped restart imap_thread (still running)")
    else:
        imap_thread = ImapThread()
        imap_thread.start()


def ui_thread():
    global FOREGROUND
    while 1:
        raw = raw_input()
        if raw == "bg":
            FOREGROUND = False
        elif raw == "fg":
            FOREGROUND = True
            on_receive()
        else:
            imap_queue.put(raw)



# android calls periodically into "on_receive"

def periodically_call(on_receive):
    periodic_thread = OnReceiveCallerThread(on_receive)
    periodic_thread.start()


class OnReceiveCallerThread(threading.Thread):
    def __init__(self, on_receive):
        self.on_receive = on_receive
        super(OnReceiveCallerThread, self).__init__()

    def run(self):
        while 1:
            on_receive()
            sleeptime = random.randint(1, 10)
            log("sleeping for", sleeptime, "seconds")
            time.sleep(sleeptime)


if __name__ == "__main__":
    start_imap_thread()
    periodically_call(on_receive)
    ui_thread()





