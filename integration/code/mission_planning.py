class MissionPlanner:
    """Plans complex missions verifying resource dependencies."""
    def __init__(self, crew_manager, inventory, maintenance):
        self.crew_manager = crew_manager
        self.inventory = inventory
        self.maintenance = maintenance

    def plan_mission(self, driver_id, car_id, mechanic_id=None):
        if self.crew_manager.get_role(driver_id) != "driver":
            return False
        
        status = self.inventory.get_car_status(car_id)
        if status == "damaged":
            if not mechanic_id or self.crew_manager.get_role(mechanic_id) != "mechanic":
                return False
            # Try to repair it first before the mission
            repaired = self.maintenance.repair_car(car_id, mechanic_id)
            if not repaired:
                return False
                
        return True
