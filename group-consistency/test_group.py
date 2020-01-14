
import random
import pytest
from itertools import count

_mcount = count()

def message_id():
    return "MsgId{}".format(next(_mcount))



class Entry:
    def __init__(self, message_id, addr, op, other_addr):
        assert op in ("add", "del")
        self.message_id = message_id
        self.addr = addr
        self.op = op
        self.other_addr = other_addr

    def __str__(self):
        return "Entry: <{}> {} {} {}".format(self.message_id, self.addr, self.op.upper(), self.other_addr)
    __repr__ = __str__

class Peer:
    def __init__(self, addr, mta):
        self.addr = addr
        self.mta = mta
        self._chats = {}
        self._known_message_ids = set()

    def process_incoming(self, from_addr, message_id, chat_id, payload):
        chat = self._chats.get(chat_id)
        if chat is None:
            chat = Chat(chat_id, mta=self.mta)
            self._chats[chat_id] = chat
            chat.add_contact(self.addr, self.addr)
        chat.receive_log(payload)

    def __eq__(self, other):
        return self.addr == other.addr

    def __ne__(self, other):
        return self.addr != other.addr

    def __hash__(self):
        return hash(self.addr)

    def __str__(self):
        return "Contact<{}>".format(self.addr)

    def __repr__(self):
        return str(self)


class Chat:
    def __init__(self, chat_id, mta):
        self.id = chat_id
        self._known_message_ids = set()
        self.mta = mta
        self.log =[]

    def __str__(self):
        return "Chat{} len={}".format(self.id, len(self.members))

    def __eq__(self, other):
        return self.id == other.id

    @property
    def members(self):
        members = []
        for entry in self.log:
            if entry.op == "add":
                members.append(entry.other_addr)
            elif entry.op == "del":
                members.remove(entry.other_addr)
        return members

    @classmethod
    def create_new(cls, chat_id, contact, mta):
        chat = cls(chat_id, mta=mta)
        # add ourself as first member
        chat.add_contact(contact, contact)
        return chat

    def add_contact_and_send(self, contact, other_contact):
        self.add_contact(contact, other_contact)
        self.send_out_last_log()

    def add_contact(self, contact, other_contact):
        if other_contact in self.members:
            raise ValueError("already a member {}".format(other_contact))
        assert isinstance(contact, str) and isinstance(other_contact, str)
        entry = Entry(message_id(), contact, "add", other_contact)
        self.log.append(entry)

    def remove_contact(self, contact, other_contact):
        assert isinstance(contact, str) and isinstance(other_contact, str)
        if other_contact not in self.members:
            raise ValueError("{} not a member".format(other_contact))
        entry = Entry(message_id(), contact, "del", other_contact)
        self.log.append(entry)

    def send_out_last_log(self):
        to_addrs = self.members[1:]
        self.mta.relay(from_addr=self.members[0], to_addrs=to_addrs, chat_id=self.id,
                       payload=self.log[-10:])

    def receive_log(self, log):
        if random.random() > 1.8:
            print("{}: failed randomly to receive log len={}".format(self, len(log)))
            return
        for entry in log:
            if entry.message_id not in self._known_message_ids:
                self._known_message_ids.add(entry.message_id)
                if entry.other_addr != self.members[0]:
                    self.log.append(entry)


class MTA:
    def __init__(self):
        self.addr2peer = {}

    def relay(self, from_addr, to_addrs, chat_id, payload):
        mid = message_id()
        for addr in to_addrs:
            peer = self.addr2peer.setdefault(addr, Peer(addr, self))
            print("relaying to {}: {}".format(addr, payload))
            peer.process_incoming(from_addr, mid, chat_id, payload)

    def ensure_consistent_member_lists(self, chat_id):
        last = None
        for addr, peer in self.addr2peer.items():
            members = peer._chats[chat_id].members
            if last is None:
                last = members
            else:
                assert sorted(last) == sorted(members)

@pytest.fixture
def mta():
    return MTA()


def test_membership_basic(mta):
    contact0 = "zero"
    chat = Chat.create_new(10, contact0, mta=mta)
    chat.add_contact_and_send(contact0, "alice")
    chat.add_contact_and_send(contact0, "bob")
    chat.add_contact_and_send(contact0, "carol")
    assert len(chat.members) == 4

    assert chat.members[0] == contact0
    assert chat.members[-1] == "carol"
    chat.remove_contact(contact0, "carol")
    chat.send_out_last_log()

    assert len(chat.members) == 3
    with pytest.raises(ValueError):
        chat.remove_contact(contact0, "unknown")

    mta.ensure_consistent_member_lists(10)

