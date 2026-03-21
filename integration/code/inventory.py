class Inventory:
    """Tracks cars, spare parts, tools, and cash balance."""
    def __init__(self, initial_cash=1000):
        self.cash = initial_cash
        self.cars = {} # car_id -> {"status": "good"|"damaged"}
        self.next_car_id = 1

    def add_car(self):
        cid = self.next_car_id
        self.cars[cid] = {"status": "good"}
        self.next_car_id += 1
        return cid

    def add_cash(self, amount):
        self.cash += amount

    def deduct_cash(self, amount):
        if self.cash < amount:
            return False
        self.cash -= amount
        return True

    def get_car_status(self, car_id):
        return self.cars.get(car_id, {}).get("status")

    def set_car_status(self, car_id, status):
        if car_id in self.cars:
            self.cars[car_id]["status"] = status
