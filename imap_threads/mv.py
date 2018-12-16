
import threading
import email
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import contextlib
import time

INBOX = "INBOX"
MVBOX = "DeltaChat"

HOST = "hq5.merlinux.eu"
USER = "t2@testrun.org"
PASSWORD = 'g6Q21uMUigE0JlFCOKt3Q6Tm8wl7'

lock_log = threading.RLock()

started = time.time()


@contextlib.contextmanager
def wlog(foldername, msg):
    t = time.time() - started
    bmsg = "%3.2f [%s] %s " % (t, foldername, msg)
    with lock_log:
        print(bmsg, "beginning")
        t0 = time.time()
    yield
    t1 = time.time()
    with lock_log:
        print(bmsg, "finish", "%3.2f" % (t1-t0))


def log(foldername, *msgs):
    t = time.time() - started
    bmsg = "%3.2f [%s]" %(t, foldername)
    with lock_log:
        print(bmsg, *msgs)


class ImapConn(object):
    def __init__(self, foldername, mvfolder=None):
        self.foldername = foldername
        self.mvfolder = mvfolder
        self.prefix = foldername
        self._thread = None
        self._tomove = []

    def connect(self):
        with wlog(self.prefix, "connect {}: {}".format(USER, PASSWORD)):
            self.conn = IMAPClient(HOST)
            self.conn.login(USER, PASSWORD)
            self.select_info = self.conn.select_folder(self.foldername)
            log(self.prefix, 'folder has %d messages' % self.select_info[b'EXISTS'])
            log(self.prefix, 'capabilities', self.conn.capabilities())

    def ensure_folder_exists(self):
        with wlog(self.prefix, "ensure_folder_exists: {}".format(self.foldername)):
            try:
                resp = self.conn.create_folder(self.foldername)
            except IMAPClientError as e:
                if "ALREADYEXISTS" in str(e):
                    return
                print("EXCEPTION:" + str(e))
            else:
                print("Server sent:", resp if resp else "nothing")

    def move(self, messages):
        with wlog(self.prefix, "move to {}: {}".format(self.mvfolder, messages)):
            resp = self.conn.move(messages, self.mvfolder)
            if resp:
                log(self.prefix, "got move response", resp)

    def perform_imap_idle(self):
        with wlog(self.prefix, "idle()"):
            res = self.conn.idle()
            interrupted = False
            while not interrupted:
                # Wait for up to 30 seconds for an IDLE response
                responses = self.conn.idle_check(timeout=30)
                log(self.prefix, "Server sent:", responses if responses else "nothing")
                to_fetch_direct = []
                for resp in responses:
                    if resp[1] == b"EXISTS":
                        id = resp[0]
                        to_fetch_direct.append(id)
                        interrupted = True
            self.conn.idle_done()
            self.fetch_messages(to_fetch_direct)

    def fetch_messages(self, to_fetch):
        with wlog(self.prefix, "fetch_messages %s" % (to_fetch,)):
            requested_fields = [
                b'UID', b'FLAGS', b"RFC822.SIZE",
                b"BODY.PEEK[HEADER.FIELDS (FROM TO CC DATE CHAT-VERSION MESSAGE-ID IN-REPLY-TO)]"
            ]
            resp = self.conn.fetch(to_fetch, requested_fields)

            for seq_id, data in resp.items():
                headers = data[requested_fields[-1].replace(b'.PEEK', b'')]
                msg = email.message_from_bytes(headers)
                chat_version = msg.get("Chat-Version")
                print('  ID %d: %d bytes, flags=%s, message-id=%s,\n'
                      '  in-reply-to=%s chat-version=%s' % (
                         seq_id,
                         data[b'RFC822.SIZE'],
                         data[b'FLAGS'],
                         msg["Message-Id"],
                         msg["In-Reply-To"],
                         chat_version,
                ))
                # check if message is a deltachat message and we have a move-folder
                if self.mvfolder and chat_version:
                    self.schedule_move(seq_id, msg)

    def schedule_move(self, seq_id, msg):
        log(self.prefix, "schedule_move", seq_id, msg["Message-Id"])
        self._tomove.append(seq_id)

    def perform_imap_jobs(self):
        with wlog(self.prefix, "perform_imap_jobs()"):
            if self._tomove:
                self.move(self._tomove)
                self._tomove[:] = []

    def perform_imap_fetch(self):
        with wlog(self.prefix, "perform_imap_fetch()"):
            pass

    def _run_in_thread(self):
        self.connect()
        if not self.mvfolder:
            self.ensure_folder_exists()
        while True:
            self.perform_imap_jobs()
            self.perform_imap_fetch()
            self.perform_imap_idle()

    def start_thread_loop(self):
        assert not self._thread
        self._thread = t = threading.Thread(target=self._run_in_thread)
        t.start()


if __name__ == "__main__":
    inbox = ImapConn(INBOX, MVBOX)
    mvbox = ImapConn(MVBOX)
    mvbox.start_thread_loop()
    inbox.start_thread_loop()
