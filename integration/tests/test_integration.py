import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from main import create_system

def test_full_happy_path():
    """Register -> Assign Role -> Enter Race -> Win Race -> Track Analytics"""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    race = sys_modules["race_manager"]
    results = sys_modules["results"]
    analytics = sys_modules["analytics"]

    # 1. Registration
    driver_id = reg.register("Dom Toretto")
    
    # 2. Crew assignment
    crew.assign_role(driver_id, "driver")
    
    # 3. Inventory (Get Car)
    car_id = inv.add_car()
    initial_cash = inv.cash
    
    # 4. Race Management
    race_id = race.create_race("Quarter Mile", entry_fee=100, prize=500)
    race.enter_race(race_id, driver_id, car_id)
    
    assert inv.cash == initial_cash - 100  # Fee deducted
    
    # 5. Results Management
    results.record_result(race_id, winner_driver_id=driver_id)
    
    # 6. Verify cross-module effects
    assert inv.cash == initial_cash - 100 + 500  # Prize awarded
    assert inv.get_car_status(car_id) == "damaged" # Winner's car gets damaged
    
    # 7. Analytics verification
    assert analytics.get_driver_wins(driver_id) == 1
    assert analytics.get_total_prize_money() == 500

def test_attempt_race_without_registration():
    """Cannot assign a role or enter a race without being registered."""
    sys_modules = create_system()
    crew = sys_modules["crew_manager"]
    
    with pytest.raises(ValueError, match="Member not registered"):
        crew.assign_role(999, "driver")

def test_mission_with_damaged_car_needs_mechanic():
    """A mission planner requires a mechanic to repair a damaged car before mission."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    mission = sys_modules["mission_planner"]
    
    # Setup driver and damaged car
    driver_id = reg.register("Brian")
    crew.assign_role(driver_id, "driver")
    car_id = inv.add_car()
    inv.set_car_status(car_id, "damaged")
    
    # Attempt mission without mechanic -> Fails
    assert not mission.plan_mission(driver_id, car_id)
    
    # Setup mechanic
    mech_id = reg.register("Tej")
    crew.assign_role(mech_id, "mechanic")
    
    # Attempt mission with mechanic -> Succeeds (mechanic repairs car)
    assert mission.plan_mission(driver_id, car_id, mechanic_id=mech_id)
    
    # Verify car is now repaired and cash explicitly deducted for repair
    assert inv.get_car_status(car_id) == "good"
    assert inv.cash == 900 # 1000 - 100 for repair
