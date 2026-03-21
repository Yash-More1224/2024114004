from registration import Registry
from crew_management import CrewManager
from inventory import Inventory
from race_management import RaceManager
from results import ResultsManager
from maintenance import MaintenanceManager
from mission_planning import MissionPlanner
from analytics import Analytics

def create_system():
    registry = Registry()
    crew_manager = CrewManager(registry)
    inventory = Inventory(initial_cash=1000)
    
    # Custom 1
    maintenance = MaintenanceManager(inventory, crew_manager)
    
    race_manager = RaceManager(crew_manager, inventory)
    results_manager = ResultsManager(race_manager, inventory)
    mission_planner = MissionPlanner(crew_manager, inventory, maintenance)
    
    # Custom 2
    analytics = Analytics(results_manager, race_manager)
    
    return {
        "registry": registry,
        "crew_manager": crew_manager,
        "inventory": inventory,
        "maintenance": maintenance,
        "race_manager": race_manager,
        "results": results_manager,
        "mission_planner": mission_planner,
        "analytics": analytics
    }

if __name__ == "__main__":
    sys = create_system()
    print("StreetRacing Manager initialised successfully.")
