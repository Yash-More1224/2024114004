class Registry:
    """Manages member registration."""
    def __init__(self):
        self.members = {} # id -> name
        self.next_id = 1

    def register(self, name):
        """Registers a new member and returns their ID."""
        cid = self.next_id
        self.members[cid] = name
        self.next_id += 1
        return cid

    def is_registered(self, cid):
        """Returns True if the ID is a registered member."""
        return cid in self.members
