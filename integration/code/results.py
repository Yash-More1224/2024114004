class ResultsManager:
    """Records race outcomes and updates inventory/stats."""
    def __init__(self, race_manager, inventory):
        self.race_manager = race_manager
        self.inventory = inventory
        self.history = []

    def record_result(self, race_id, winner_driver_id):
        if race_id not in self.race_manager.races:
            raise ValueError("Race not found")
        
        race = self.race_manager.races[race_id]
        entries = [d for d, c in race["entries"]]
        if winner_driver_id not in entries:
            raise ValueError("Winner did not enter this race")
        
        # Award prize
        self.inventory.add_cash(race["prize"])
        
        # Update history
        self.history.append({"race_id": race_id, "winner": winner_driver_id})
        
        # Damage the winning car (simulate racing wear/tear)
        winner_car_id = next(c for d, c in race["entries"] if d == winner_driver_id)
        self.inventory.set_car_status(winner_car_id, "damaged")
        
        return True
