from registration import Registry
from crew_management import CrewManager
from inventory import Inventory
from race_management import RaceManager
from results import ResultsManager
from maintenance import MaintenanceManager
from mission_planning import MissionPlanner
from analytics import Analytics


def prompt_int(label):
    while True:
        value = input(label).strip()
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid integer.")


def print_menu():
    print("\n=== StreetRace Manager CLI ===")
    print("1. Register crew member")
    print("2. Assign role to member")
    print("3. Add car")
    print("4. Add cash")
    print("5. Set car status")
    print("6. Create race")
    print("7. Enter race")
    print("8. Record race result")
    print("9. Plan mission")
    print("10. Repair car")
    print("11. Show driver wins")
    print("12. Show total prize money")
    print("13. Show system state")
    print("0. Exit")

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


def show_state(system):
    registry = system["registry"]
    crew_manager = system["crew_manager"]
    inventory = system["inventory"]
    race_manager = system["race_manager"]
    results = system["results"]

    print("\n--- Current State ---")
    print(f"Members: {registry.members}")
    print(f"Roles: {crew_manager.roles}")
    print(f"Cash: {inventory.cash}")
    print(f"Cars: {inventory.cars}")
    print(f"Races: {race_manager.races}")
    print(f"Results history: {results.history}")


def run_cli(system):
    registry = system["registry"]
    crew_manager = system["crew_manager"]
    inventory = system["inventory"]
    maintenance = system["maintenance"]
    race_manager = system["race_manager"]
    results = system["results"]
    mission_planner = system["mission_planner"]
    analytics = system["analytics"]

    print("StreetRacing Manager initialised successfully.")
    print("Use the menu to run module operations interactively.")

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                name = input("Member name: ").strip()
                member_id = registry.register(name)
                print(f"Registered '{name}' with ID {member_id}.")

            elif choice == "2":
                member_id = prompt_int("Member ID: ")
                role = input("Role (driver/mechanic/strategist): ").strip()
                crew_manager.assign_role(member_id, role)
                print(f"Assigned role '{role}' to member {member_id}.")

            elif choice == "3":
                car_id = inventory.add_car()
                print(f"Added car with ID {car_id}.")

            elif choice == "4":
                amount = prompt_int("Amount to add: ")
                inventory.add_cash(amount)
                print(f"Cash updated. New balance: {inventory.cash}")

            elif choice == "5":
                car_id = prompt_int("Car ID: ")
                status = input("Status (good/damaged): ").strip()
                if status not in ["good", "damaged"]:
                    print("Invalid status. Use 'good' or 'damaged'.")
                    continue
                inventory.set_car_status(car_id, status)
                print(f"Car {car_id} status set to '{status}'.")

            elif choice == "6":
                race_name = input("Race name: ").strip()
                entry_fee = prompt_int("Entry fee: ")
                prize = prompt_int("Prize amount: ")
                race_id = race_manager.create_race(race_name, entry_fee, prize)
                print(f"Race '{race_name}' created with ID {race_id}.")

            elif choice == "7":
                race_id = prompt_int("Race ID: ")
                driver_id = prompt_int("Driver ID: ")
                car_id = prompt_int("Car ID: ")
                race_manager.enter_race(race_id, driver_id, car_id)
                print(f"Driver {driver_id} entered race {race_id} with car {car_id}.")

            elif choice == "8":
                race_id = prompt_int("Race ID: ")
                winner_id = prompt_int("Winner driver ID: ")
                results.record_result(race_id, winner_id)
                print(f"Result recorded for race {race_id}. Winner: {winner_id}.")

            elif choice == "9":
                driver_id = prompt_int("Driver ID: ")
                car_id = prompt_int("Car ID: ")
                mechanic_text = input("Mechanic ID (optional, press Enter to skip): ").strip()
                mechanic_id = int(mechanic_text) if mechanic_text else None
                success = mission_planner.plan_mission(driver_id, car_id, mechanic_id)
                print(f"Mission planning result: {success}")

            elif choice == "10":
                car_id = prompt_int("Car ID: ")
                mechanic_id = prompt_int("Mechanic ID: ")
                repaired = maintenance.repair_car(car_id, mechanic_id)
                print(f"Repair result: {repaired}")

            elif choice == "11":
                driver_id = prompt_int("Driver ID: ")
                wins = analytics.get_driver_wins(driver_id)
                print(f"Driver {driver_id} wins: {wins}")

            elif choice == "12":
                total_prize = analytics.get_total_prize_money()
                print(f"Total prize money awarded so far: {total_prize}")

            elif choice == "13":
                show_state(system)

            elif choice == "0":
                print("Exiting StreetRace Manager CLI.")
                break

            else:
                print("Invalid option. Choose from the menu.")

        except ValueError as error:
            print(f"Operation failed: {error}")

if __name__ == "__main__":
    system = create_system()
    run_cli(system)
