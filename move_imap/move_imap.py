import os
import threading
import click
import atexit
import email
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import contextlib
import time
from persistentdict import PersistentDict

INBOX = "INBOX"
MVBOX = "DeltaChat"
DC_CONSTANT_MOVE = 1
DC_CONSTANT_STAY = 2
DC_CONSTANT_STUCK = 3


def db_folder_attr(name):
    def fget(s):
        return s.db_folder.get(name, 1)
    def fset(s, val):
        s.db_folder[name] = val
    return property(fget, fset, None, None)

lock_log = threading.RLock()
started = time.time()


class ImapConn(object):
    def __init__(self, db, foldername, conn_info):
        self.db = db
        self.foldername = foldername
        self._thread = None
        self.MHOST, self.MUSER, self.MPASSWORD = conn_info
        self.event_initial_polling_complete = threading.Event()

        # persistent database state below
        self.db_folder = self.db.setdefault(foldername, {})
        self.db_messages = self.db.setdefault(":message-full", {})

    last_sync_uid = db_folder_attr("last_sync_uid")

    @contextlib.contextmanager
    def wlog(self, msg):
        t = time.time() - started
        with lock_log:
            print("%03.2f [%s] %s -->" % (t, self.foldername, msg))
            t0 = time.time()
        yield
        t1 = time.time()
        with lock_log:
            print("%03.2f [%s] ... finish %s (%3.2f secs)" % (t1-started, self.foldername, msg, t1-t0))

    def log(self, *msgs):
        t = time.time() - started
        bmsg = "%03.2f [%s]" %(t, self.foldername)
        with lock_log:
            print(bmsg, *msgs)

    def connect(self):
        with self.wlog("IMAP_CONNECT {}: {}".format(self.MUSER, self.MPASSWORD)):
            self.conn = IMAPClient(self.MHOST)
            self.conn.login(self.MUSER, self.MPASSWORD)
            self.select_info = self.conn.select_folder(self.foldername)
            self.log('folder has %d messages' % self.select_info[b'EXISTS'])
            self.log('capabilities', self.conn.capabilities())

    def ensure_folder_exists(self):
        with self.wlog("ensure_folder_exists: {}".format(self.foldername)):
            try:
                resp = self.conn.create_folder(self.foldername)
            except IMAPClientError as e:
                if "ALREADYEXISTS" in str(e):
                    return
                print("EXCEPTION:" + str(e))
            else:
                print("Server sent:", resp if resp else "nothing")

    def move(self, messages):
        resp = self.conn.move(messages, MVBOX)
        self.log("IMAP_MOVE to {}: {} -> done".format(MVBOX, messages))
        if resp:
            self.log("got move response", resp)

    def perform_imap_idle(self):
        if self.foldername == INBOX and self.pending_imap_jobs:
            self.log("perform_imap_idle skipped because jobs are pending")
            return
        with self.wlog("IMAP_IDLE()"):
            res = self.conn.idle()
            interrupted = False
            while not interrupted:
                # Wait for up to 30 seconds for an IDLE response
                responses = self.conn.idle_check(timeout=30)
                self.log("Server sent:", responses if responses else "nothing")
                for resp in responses:
                    if resp[1] == b"EXISTS":
                        # we ignore what is returned and just let
                        # perform_imap_fetch look since lastseen
                        # id = resp[0]
                        interrupted = True
            resp = self.conn.idle_done()

    def perform_imap_fetch(self):
        range = "%s:*" % (self.last_sync_uid + 1,)
        with self.wlog("IMAP_PERFORM_FETCH %s" % (range,)):
            requested_fields = [
                b"RFC822.SIZE", b'FLAGS',
                b"BODY.PEEK[HEADER.FIELDS (FROM TO CC DATE CHAT-VERSION MESSAGE-ID IN-REPLY-TO)]"
            ]
            resp = self.conn.fetch(range, requested_fields)
            timestamp_fetch = time.time()
            for uid in sorted(resp):  # get lower uids first
                if uid < self.last_sync_uid:
                    self.log("IMAP-ODDITY: ignoring bogus uid %s, it is lower than min-requested %s" %(
                             uid, self.last_sync_uid))
                    continue
                data = resp[uid]
                headers = data[requested_fields[-1].replace(b'.PEEK', b'')]
                msg_headers = email.message_from_bytes(headers)
                message_id = normalized_messageid(msg_headers)
                chat_version = msg_headers.get("Chat-Version")
                in_reply_to = msg_headers.get("In-Reply-To", "").lower()

                if not self.has_message(normalized_messageid(msg_headers)):
                    self.log('fetching body of ID %d: %d bytes, message-id=%s '
                             'in-reply-to=%s chat-version=%s' % (
                             uid, data[b'RFC822.SIZE'], message_id, in_reply_to, chat_version,))
                    fetchbody_resp = self.conn.fetch(uid, [b'BODY.PEEK[]'])
                    msg = email.message_from_bytes(fetchbody_resp[uid][b'BODY[]'])
                    msg.fetch_retrieve_time = timestamp_fetch
                    msg.stuck_state = False
                    msg.foldername = self.foldername
                    msg.target_foldername = self.foldername
                    msg.uid = uid
                    self.store_message(message_id, msg)
                else:
                    msg = self.get_message_from_db(message_id)
                    self.log('fetching-from-db: ID %s message-id=%s' % (uid, message_id))
                    if msg.foldername != self.foldername:
                        self.log("detected moved message", message_id)
                        msg.foldername = msg.target_foldername = self.foldername
                        msg.uid = -1  # indicates "don't move again!"

                if self.foldername == INBOX:
                    if self.resolve_move_status(msg):
                        # message is STAY or MOVE, not stuck.
                        # see if there are stuck messages in-reply-to to our currnet msg
                        # NOTE: should be one sql-statement to find the
                        # possibly multiple messages that waited on us
                        for dbmid, dbmsg in self.db_messages.items():
                            if dbmsg.stuck_state:
                                if dbmsg["In-Reply-To"].lower() == message_id:
                                    self.log("resolving pending message", dbmid)
                                    # resolving the dependent message must work now
                                    assert self.resolve_move_status(dbmsg)

                if not self.has_message(message_id):
                    self.store_message(message_id, msg)

                self.last_sync_uid = max(uid, self.last_sync_uid)

        self.log("last-sync-uid after fetch:", self.last_sync_uid)
        self.db.sync()

    def resolve_move_status(self, msg):
        """ Return True if message's move-status is determined (i.e. it is not stuck)"""
        message_id = normalized_messageid(msg)
        res = self.shall_move(msg)
        if res == DC_CONSTANT_MOVE:
            self.schedule_move(msg)
            msg.stuck_state = False
        elif res == DC_CONSTANT_STAY:
            self.log("STAY uid=%s message-id=%s" % (msg.uid, message_id))
            msg.stuck_state = False
        elif res == DC_CONSTANT_STUCK:
            msg.stuck_state = True
            self.log("STUCK uid=%s message-id=%s in-reply-to=%s" %(msg.uid, message_id, msg["In-Reply-To"]))
            return False
        return True

    def shall_move(self, msg):
        """ Return an integer indicating outcome for the determination
        if the specified message should be moved:

        DC_CONSTANT_STAY:  message should not be moved
        DC_CONSTANT_MOVE:  message should be moved
        DC_CONSTANT_STUCK: message should be reconsidered, could not determine a parent message
        """
        assert self.foldername == INBOX
        # here we determine if a given msg needs to be moved.
        # This function works with the DB, does not perform any IMAP
        # commands.
        if msg.uid == -1:
            return DC_CONSTANT_STAY
        self.log("shall_move %s " %(normalized_messageid(msg)))
        last_dc_count = 0
        while 1:
            last_dc_count = (last_dc_count + 1) if is_dc_message(msg) else 0
            in_reply_to = normalized_messageid(msg.get("In-Reply-To", ""))
            if not in_reply_to:
                type_msg = "DC" if last_dc_count else "CLEAR"
                self.log("detected thread-start %s message" % type_msg, normalized_messageid(msg))
                return DC_CONSTANT_MOVE if last_dc_count > 0 else DC_CONSTANT_STAY

            newmsg = self.get_message_from_db(in_reply_to)
            if not newmsg:
                self.log("failed to fetch from db:", in_reply_to)
                # we don't have the parent message ... maybe because
                # it hasn't arrived (yet), was deleted or we failed to
                # scan/fetch it:
                if last_dc_count >= 4:
                    self.log("no thread-start found, but last 4 messages were DC")
                    return DC_CONSTANT_MOVE
                else:
                    self.log("stuck: missing parent, last_dc_count=%x" %(last_dc_count, ))
                    return DC_CONSTANT_STUCK
            elif self.is_moved_message(newmsg):
                self.log("parent was a moved message")
                return DC_CONSTANT_MOVE
            else:
                msg = newmsg
        assert 0, "should never arrive here"

    def schedule_move(self, msg):
        message_id = normalized_messageid(msg)
        assert msg.foldername == INBOX and msg.target_foldername == INBOX
        msg.target_foldername = MVBOX
        self.log("scheduling move message-id=%s" % (message_id))
        self.pending_imap_jobs = True

    def is_moved_message(self, msg):
        message_id = normalized_messageid(msg)
        return msg.foldername == MVBOX or msg.target_foldername == MVBOX

    def has_message(self, message_id):
        assert isinstance(message_id, str)
        return message_id in self.db_messages

    def get_message_from_db(self, message_id):
        return self.db_messages.get(normalized_messageid(message_id))

    def store_message(self, message_id, msg):
        mid2 = normalized_messageid(msg)
        message_id = normalized_messageid(message_id)
        assert message_id == mid2
        assert message_id not in self.db_messages, message_id
        assert msg.foldername in (MVBOX, INBOX)
        self.db_messages[message_id] = msg
        self.log("stored new message message-id=%s" %(message_id,))

    def forget_about_too_old_stuck_messages(self):
        # some housekeeping but not sure if neccessary
        # because the involved sql-statements
        # probably don't care if there are some foreever-stuck messages
        now = time.time()
        for dbmid, dbmsg in self.db_messages.items():
            if dbmsg.stuck_state:
                delay = now - dbmsg.fetch_retrieve_time
                if delay > self.STUCKTIMEOUT:
                    dbmsg.stuck_state = False
                    self.log("STUCKTIMEOUT: unstucked", dbmid)

    def perform_imap_jobs(self):
        with self.wlog("perform_imap_jobs()"):
            if self.foldername == INBOX:
                to_move_uids = []
                to_move_msgs = []

                # determine all uids of messages that are to be moved
                for dbmid, dbmsg in self.db_messages.items():
                    if dbmsg.foldername == INBOX and dbmsg.target_foldername == MVBOX:
                        assert dbmsg.uid > 0
                        to_move_uids.append(dbmsg.uid)
                        to_move_msgs.append(dbmsg)
                if to_move_uids:
                    self.move(to_move_uids)
                for dbmsg in to_move_msgs:
                    dbmsg.foldername = MVBOX
                    dbmsg.uid = 0
            self.pending_imap_jobs = False

    def _run_in_thread(self):
        self.connect()
        if self.foldername == MVBOX:
            self.ensure_folder_exists()
        else:
            # INBOX loop should wait until MVBOX polled once
            mvbox.event_initial_polling_complete.wait()
        now = time.time()
        while True:
            self.perform_imap_jobs()
            self.perform_imap_fetch()
            if self.foldername == MVBOX:
                # signal that MVBOX has polled once
                self.event_initial_polling_complete.set()
            elif self.foldername == INBOX:
                # it's not clear we need to do this housekeeping
                # depends on the SQL statements
                self.forget_about_too_old_stuck_messages()
            self.perform_imap_idle()

    def start_thread_loop(self):
        assert not self._thread
        self._thread = t = threading.Thread(target=self._run_in_thread)
        t.start()


def is_dc_message(msg):
    return msg and msg.get("Chat-Version")

def normalized_messageid(msg):
    if isinstance(msg, str):
        return msg.lower()
    return msg["Message-ID"].lower()



@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--stucktimeout", type=int, default=3600,
              help="(default 3600) seconds which a message is still considered for moving "
                   "even though it has no determined thread-start message")
@click.argument("imaphost", type=str, required=True)
@click.argument("login-user", type=str, required=True)
@click.argument("login-password", type=str, required=True)
@click.pass_context
def main(context, imaphost, login_user, login_password, stucktimeout):
    global mvbox
    db = PersistentDict("testmv.db")
    conn_info = (imaphost, login_user, login_password)
    inbox = ImapConn(db, INBOX, conn_info=conn_info)
    inbox.STUCKTIMEOUT = stucktimeout
    mvbox = ImapConn(db, MVBOX, conn_info=conn_info)
    mvbox.start_thread_loop()
    inbox.start_thread_loop()


if __name__ == "__main__":
    main()
