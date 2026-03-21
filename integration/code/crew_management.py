class CrewManager:
    """Manages role assignments and checks for registered members."""
    def __init__(self, registry):
        self.registry = registry
        self.roles = {} # cid -> role

    def assign_role(self, cid, role):
        if not self.registry.is_registered(cid):
            raise ValueError("Member not registered")
        if role not in ["driver", "mechanic", "strategist"]:
            raise ValueError("Invalid role")
        self.roles[cid] = role

    def get_role(self, cid):
        return self.roles.get(cid)

    def get_members_by_role(self, role):
        return [cid for cid, r in self.roles.items() if r == role]
