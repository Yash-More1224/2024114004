class RaceManager:
    """Manages racing events and entry verification."""
    def __init__(self, crew_manager, inventory):
        self.crew_manager = crew_manager
        self.inventory = inventory
        self.races = {} # race_id -> dict
        self.next_race_id = 1

    def create_race(self, name, entry_fee, prize):
        rid = self.next_race_id
        self.races[rid] = {
            "name": name, 
            "entry_fee": entry_fee, 
            "prize": prize, 
            "entries": []
        }
        self.next_race_id += 1
        return rid

    def enter_race(self, race_id, driver_id, car_id):
        if race_id not in self.races:
            raise ValueError("Race not found")
        if self.crew_manager.get_role(driver_id) != "driver":
            raise ValueError("Only drivers can enter races")
        if self.inventory.get_car_status(car_id) != "good":
            raise ValueError("Car is damaged")
        
        fee = self.races[race_id]["entry_fee"]
        if not self.inventory.deduct_cash(fee):
            raise ValueError("Not enough cash for entry fee")
            
        self.races[race_id]["entries"].append((driver_id, car_id))
        return True
