
import pytest
from itertools import count

_mcount = count()

def message_id():
    return "MsgId{}".format(next(_mcount))



class Entry:
    def __init__(self, message_id, contact, op, other_contact):
        assert op in ("add", "del")
        self.message_id = message_id
        self.contact = contact
        self.op = op
        self.other_contact = other_contact

    def __str__(self):
        return "Entry: <{}> {} {} {}".format(self.message_id, self.contact, self.op, self.other_contact)


class Contact:
    def __init__(self, addr):
        self.addr = addr
        self._chats = {}

    def receive_log(self, chat_id, log):
        chat = self._chats.get(chat_id)
        if chat is None:
            chat = Chat(chat_id)
            self._chats[chat_id] = chat
        chat.receive_log(log)

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
    def __init__(self, chat_id):
        self.id = id
        self._known_message_ids = set()
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
                members.append(entry.other_contact)
            elif entry.op == "del":
                members.remove(entry.other_contact)
        return members

    @classmethod
    def create_new(cls, chat_id, contact):
        chat = cls(chat_id)
        # add ourself as first member
        chat.add_contact(contact, contact)
        return chat

    def add_contact(self, contact, other_contact):
        if other_contact in self.members:
            return
        assert isinstance(contact, Contact) and isinstance(other_contact, Contact)
        entry = Entry(message_id(), contact, "add", other_contact)
        self.log.append(Entry(message_id(), contact, "add", other_contact))

    def remove_contact(self, contact, other_contact):
        if other_contact not in self.members:
            raise ValueError("{} not a member".format(other_contact))
        self.log.append(Entry(message_id(), contact, "del", other_contact))

    def send_out_last_log(self):
        entry = self.log[-1]
        for member in self.members[1:]:
            member.receive_log(chat_id=self.id, log=self.log[-1:])

    def receive_log(self, log):
        for entry in log:
            if entry.message_id not in self._known_message_ids:
                if entry.op == "add":
                    self.add_contact(entry.contact, entry.other_contact)
                else:
                    self.remove_contact(entry.contact, entry.other_contact)
                self._known_message_ids.add(entry.message_id)

def test_membership_basic():

    contact0 = Contact("zero")
    chat = Chat.create_new(10, contact0)
    chat.add_contact(contact0, Contact("alice"))
    chat.send_out_last_log()
    chat.add_contact(contact0, Contact("bob"))
    chat.send_out_last_log()
    chat.add_contact(contact0, Contact("carol"))
    chat.send_out_last_log()

    assert len(chat.members) == 4

    assert chat.members[0] == contact0
    assert chat.members[-1].addr == "carol"
    chat.remove_contact(contact0, chat.members[-1])
    assert len(chat.members) == 3
    with pytest.raises(ValueError):
        chat.remove_contact(contact0, Contact("unknown"))
