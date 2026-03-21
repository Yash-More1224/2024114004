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


def test_registered_non_driver_cannot_enter_race():
    """A registered member with non-driver role cannot be entered in a race."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    race = sys_modules["race_manager"]

    strategist_id = reg.register("Roman")
    crew.assign_role(strategist_id, "strategist")
    car_id = inv.add_car()
    race_id = race.create_race("Night Sprint", entry_fee=100, prize=300)

    with pytest.raises(ValueError, match="Only drivers can enter races"):
        race.enter_race(race_id, strategist_id, car_id)


def test_damaged_car_cannot_enter_race():
    """Race entry rejects damaged vehicles from inventory."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    race = sys_modules["race_manager"]

    driver_id = reg.register("Letty")
    crew.assign_role(driver_id, "driver")
    car_id = inv.add_car()
    inv.set_car_status(car_id, "damaged")
    race_id = race.create_race("Tunnel Run", entry_fee=100, prize=350)

    with pytest.raises(ValueError, match="Car is damaged"):
        race.enter_race(race_id, driver_id, car_id)


def test_race_entry_fails_if_inventory_cash_insufficient():
    """RaceManager depends on Inventory.deduct_cash for entry-fee enforcement."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    race = sys_modules["race_manager"]

    driver_id = reg.register("Han")
    crew.assign_role(driver_id, "driver")
    car_id = inv.add_car()
    inv.cash = 50

    race_id = race.create_race("Harbor Dash", entry_fee=100, prize=250)

    with pytest.raises(ValueError, match="Not enough cash for entry fee"):
        race.enter_race(race_id, driver_id, car_id)

    assert race.races[race_id]["entries"] == []


def test_results_reject_winner_not_in_entries_and_do_not_pay_prize():
    """Results must validate race entries before awarding money."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    race = sys_modules["race_manager"]
    results = sys_modules["results"]

    driver_1 = reg.register("Dom")
    driver_2 = reg.register("Brian")
    crew.assign_role(driver_1, "driver")
    crew.assign_role(driver_2, "driver")

    car_id = inv.add_car()
    race_id = race.create_race("Dockline", entry_fee=100, prize=500)
    race.enter_race(race_id, driver_1, car_id)
    cash_after_entry = inv.cash

    with pytest.raises(ValueError, match="Winner did not enter this race"):
        results.record_result(race_id, winner_driver_id=driver_2)

    assert inv.cash == cash_after_entry
    assert results.history == []


def test_mission_fails_with_wrong_mechanic_role_for_damaged_car():
    """Mission planning must refuse damaged-car mission when helper is not a mechanic."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    mission = sys_modules["mission_planner"]

    driver_id = reg.register("Mia")
    helper_id = reg.register("Jakob")
    crew.assign_role(driver_id, "driver")
    crew.assign_role(helper_id, "strategist")

    car_id = inv.add_car()
    inv.set_car_status(car_id, "damaged")

    assert mission.plan_mission(driver_id, car_id, mechanic_id=helper_id) is False
    assert inv.get_car_status(car_id) == "damaged"


def test_mission_fails_when_repair_needed_but_cash_too_low():
    """Mission planner + maintenance + inventory interaction on repair-cost failure."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    mission = sys_modules["mission_planner"]

    driver_id = reg.register("Suki")
    mechanic_id = reg.register("Tej")
    crew.assign_role(driver_id, "driver")
    crew.assign_role(mechanic_id, "mechanic")

    car_id = inv.add_car()
    inv.set_car_status(car_id, "damaged")
    inv.cash = 80

    assert mission.plan_mission(driver_id, car_id, mechanic_id=mechanic_id) is False
    assert inv.cash == 80
    assert inv.get_car_status(car_id) == "damaged"


def test_analytics_aggregates_multiple_results_correctly():
    """Analytics should reflect wins per driver and total prize money across races."""
    sys_modules = create_system()
    reg = sys_modules["registry"]
    crew = sys_modules["crew_manager"]
    inv = sys_modules["inventory"]
    race = sys_modules["race_manager"]
    results = sys_modules["results"]
    analytics = sys_modules["analytics"]

    driver_a = reg.register("Dom")
    driver_b = reg.register("Brian")
    crew.assign_role(driver_a, "driver")
    crew.assign_role(driver_b, "driver")

    car_a = inv.add_car()
    car_b = inv.add_car()

    race_1 = race.create_race("Run 1", entry_fee=50, prize=200)
    race.enter_race(race_1, driver_a, car_a)
    results.record_result(race_1, winner_driver_id=driver_a)

    inv.set_car_status(car_a, "good")
    race_2 = race.create_race("Run 2", entry_fee=50, prize=300)
    race.enter_race(race_2, driver_a, car_a)
    race.enter_race(race_2, driver_b, car_b)
    results.record_result(race_2, winner_driver_id=driver_b)

    assert analytics.get_driver_wins(driver_a) == 1
    assert analytics.get_driver_wins(driver_b) == 1
    assert analytics.get_total_prize_money() == 500
