
import pytest

class Peer:
    def __init__(self, id):
        self.id = id
        self.chats = {}

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    def create_chat(self):
        chat = Chat(self, len(self.chats))
        self.chats[chat.id] = chat
        return chat

class Chat:
    def __init__(self, peer, id):
        self.id = id
        self.members = [peer]

    def add_member(self, peer):
        assert isinstance(peer, Peer)
        self.members.append(peer)

    def remove_member(self, peer):
        print(peer, self.members)
        if peer not in self.members:
            raise ValueError("peer{} not a member".format(peer.id))
        self.members.remove(peer)


def test_membership_basic():

    peer0 = Peer(0)
    chat = peer0.create_chat()

    for i in range(1, 6):
        new_peer = Peer(i)
        chat.add_member(new_peer)

    assert len(chat.members) == 6

    assert chat.members[0] == peer0
    chat.remove_member(chat.members[-1])
    assert len(chat.members) == 5
    with pytest.raises(ValueError):
        chat.remove_member(Peer(100))

