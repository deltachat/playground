from __future__ import print_function

import threading
import queue
import time


def log(*args):
    t = threading.current_thread()
    print(t, *args)


class ImapThread(threading.Thread):
    def run(self):
        try:
            while 1:
                should_stop = perform_imap_jobs()
                if should_stop:
                    log("terminating loop")
                    break
                log("calling imap-idle")
                time.sleep(10)
        finally:
            print("finished imap threaD")



def perform_imap_jobs():
    should_stop = False
    while 1:
        log("perform_imap_jobs: attempting to get a job")
        try:
            x = imap_queue.get(timeout=0.1)
        except queue.Empty:
            break
        else:
            log("processing imap job:", x)
            if x == "terminate":
                should_stop = True
                break
    log("perform_imap_jobs: finished loop")
    return should_stop




def on_receive():
    if imap_thread.is_alive():
        log("skipping on_receive activity, imapthread is still alive")
        return
    perform_imap_jobs()


imap_queue = queue.Queue()
imap_thread = None

def start_foreground():
    global imap_thread
    if imap_thread is not None and imap_thread.is_alive():
        log("skipped restart imap_thread (still running)")
    else:
        imap_thread = ImapThread()
        imap_thread.start()


def ui_thread():
    while 1:
        raw = raw_input()
        if raw == "bg":
            imap_queue.put("terminate")
        elif raw == "fg":
            start_foreground()
        else:
            imap_queue.put(raw)



# android calls periodically into "on_receive"

def periodically_call(on_receive):
    periodic_thread = PeriodicThread(on_receive)
    periodic_thread.start()


class PeriodicThread(threading.Thread):
    def __init__(self, on_receive):
        self.on_receive = on_receive
        super(PeriodicThread, self).__init__()

    def run(self):
        while 1:
            on_receive()
            time.sleep(5)


if __name__ == "__main__":
    start_foreground()
    periodically_call(on_receive)
    ui_thread()





