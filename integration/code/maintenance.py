class MaintenanceManager:
    """Custom module: Schedules maintenance and assigns mechanics for car repair."""
    def __init__(self, inventory, crew_manager):
        self.inventory = inventory
        self.crew_manager = crew_manager

    def repair_car(self, car_id, mechanic_id):
        if self.crew_manager.get_role(mechanic_id) != "mechanic":
            raise ValueError("Only mechanics can repair cars")
            
        if self.inventory.get_car_status(car_id) != "damaged":
            return False # no repair needed
            
        if self.inventory.deduct_cash(100):
            self.inventory.set_car_status(car_id, "good")
            return True
            
        return False
