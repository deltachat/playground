import os
import threading
import atexit
import email
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import contextlib
import time
from persistentdict import PersistentDict

INBOX = "INBOX"
MVBOX = "DeltaChat"

HOST = "hq5.merlinux.eu"
USER = os.environ["MUSER"]
PASSWORD = os.environ["MPASSWORD"]

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
    def __init__(self, db, foldername, mvfolder=None):
        self.db = db
        self.db_folder = self.db.setdefault(foldername, {})
        self.db_messages = self.db.setdefault(":messages", {})
        self.tomove = self.db_folder.get("tomove", []) if mvfolder else None
        self.foldername = foldername
        self.mvfolder = mvfolder
        self.prefix = foldername
        self._thread = None

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
            #if resp:
            #    log(self.prefix, "got move response", resp)

    def perform_imap_idle(self):
        if self.tomove:
            log(self.prefix, "perform_imap_idle skipped because jobs are pending")
            return
        with wlog(self.prefix, "idle()"):
            res = self.conn.idle()
            interrupted = False
            while not interrupted:
                # Wait for up to 30 seconds for an IDLE response
                responses = self.conn.idle_check(timeout=30)
                log(self.prefix, "Server sent:", responses if responses else "nothing")
                for resp in responses:
                    if resp[1] == b"EXISTS":
                        # id = resp[0]
                        interrupted = True
            resp = self.conn.idle_done()

    def last_seen_msg():
        def fget(s):
            return s.db_folder.get("last_seen_msg", 1)
        def fset(s, val):
            s.db_folder["last_seen_msg"] = val
        return property(fget, fset, None, None)

    last_seen_msg = last_seen_msg()


    def fetch_messages(self):
        range = "%s:*" % (self.last_seen_msg + 1,)
        with wlog(self.prefix, "fetch_message %s" % (range,)):
            requested_fields = [
                b'FLAGS', b"RFC822.SIZE",
                b"BODY.PEEK[HEADER.FIELDS (FROM TO CC DATE CHAT-VERSION MESSAGE-ID IN-REPLY-TO)]"
            ]
            resp = self.conn.fetch(range, requested_fields)
            for seq_id in sorted(resp):
                data = resp[seq_id]
                headers = data[requested_fields[-1].replace(b'.PEEK', b'')]
                msg = email.message_from_bytes(headers)
                chat_version = msg.get("Chat-Version")
                in_reply_to = msg.get("In-Reply-To")
                print('  ID %d: %d bytes, flags=%s, message-id=%s,\n'
                      '  in-reply-to=%s chat-version=%s' % (
                         seq_id,
                         data[b'RFC822.SIZE'],
                         data[b'FLAGS'],
                         msg["Message-Id"],
                         in_reply_to,
                         chat_version,
                ))
                if not self.has_message(msg):
                    # if we have a move-folder, move on certain conditions
                    if self.mvfolder:
                        if chat_version:
                            log(self.prefix, "detected direct dc message", msg["Message-Id"])
                            self.schedule_move(seq_id, msg)
                        elif in_reply_to:
                            orig_msg = self.get_message(in_reply_to)
                            if orig_msg and orig_msg.get("Chat-Version"):
                                log(self.prefix, "detected non-dc reply to dc message", msg["Message-Id"])
                                self.schedule_move(seq_id, msg)
                    self.store_message_headers(msg)

                self.last_seen_msg = max(seq_id, self.last_seen_msg)

    def schedule_move(self, msgid, msg):
        log(self.prefix, "scheduling move", msgid, "message-id=" + msg["Message-Id"])
        self.tomove.append(msgid)

    def has_message(self, msg):
        msg_id = msg if isinstance(msg, str) else msg["Message-Id"]
        return msg_id.lower() in self.db_messages

    def get_message(self, msg_id):
        return self.db_messages.get(msg_id.lower())

    def store_message_headers(self, msg):
        self.db_messages[msg["message-id"].lower()] = msg

    def perform_imap_jobs(self):
        with wlog(self.prefix, "perform_imap_jobs()"):
            if self.tomove:
                self.move(self.tomove)
                self.tomove[:] = []

    def perform_imap_fetch(self):
        with wlog(self.prefix, "perform_imap_fetch()"):
            self.fetch_messages()

    def _run_in_thread(self):
        self.connect()
        if not self.mvfolder:
            self.ensure_folder_exists()
        now = time.time()
        while True:
            self.perform_imap_jobs()
            self.perform_imap_fetch()
            self.perform_imap_idle()
            if time.time() - now > 10:
                self.sync_db()
                now = time.time()

    def sync_db(self):
        with wlog(self.prefix, "syncing db to file"):
            self.db.sync()

    def start_thread_loop(self):
        assert not self._thread
        self._thread = t = threading.Thread(target=self._run_in_thread)
        t.start()


if __name__ == "__main__":
    db = PersistentDict("testmv.db")
    inbox = ImapConn(db, INBOX, MVBOX)
    mvbox = ImapConn(db, MVBOX)
    # atexit.register(inbox.sync_db)
    # atexit.register(mvbox.sync_db)
    mvbox.start_thread_loop()
    inbox.start_thread_loop()
