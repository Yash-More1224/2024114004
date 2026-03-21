class Analytics:
    """Custom module: Tracks crew performance and win rates."""
    def __init__(self, results_manager, race_manager):
        self.results_manager = results_manager
        self.race_manager = race_manager

    def get_driver_wins(self, driver_id):
        wins = 0
        for r in self.results_manager.history:
            if r["winner"] == driver_id:
                wins += 1
        return wins

    def get_total_prize_money(self):
        total = 0
        for r in self.results_manager.history:
            race = self.race_manager.races[r["race_id"]]
            total += race["prize"]
        return total
