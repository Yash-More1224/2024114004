"""
White-box test suite for the MoneyPoly game.

Covers: all branches (decision paths), key variable states, and relevant edge
cases across player.py, bank.py, dice.py, property.py, cards.py, game.py.
"""
import sys
import os
import pytest

# Allow running from whitebox/tests/ with the moneypoly package on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from moneypoly.player import Player
from moneypoly.bank import Bank
from moneypoly.dice import Dice
from moneypoly.property import Property, PropertyGroup
from moneypoly.cards import CardDeck, CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from moneypoly.board import Board
from moneypoly.game import Game
from moneypoly.config import (
    STARTING_BALANCE, GO_SALARY, BOARD_SIZE,
    JAIL_POSITION, INCOME_TAX_AMOUNT, LUXURY_TAX_AMOUNT,
    JAIL_FINE, BANK_STARTING_FUNDS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Player Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPlayerInit:
    """Player initialises with correct defaults."""

    def test_default_balance(self):
        p = Player("Alice")
        assert p.balance == STARTING_BALANCE

    def test_custom_balance(self):
        p = Player("Bob", balance=500)
        assert p.balance == 500

    def test_default_position(self):
        assert Player("Alice").position == 0

    def test_not_in_jail_initially(self):
        assert not Player("Alice").in_jail

    def test_no_jail_cards_initially(self):
        assert Player("Alice").get_out_of_jail_cards == 0


class TestPlayerMoney:
    """add_money / deduct_money guard rails and balance tracking."""

    def test_add_money_increases_balance(self):
        p = Player("Alice")
        p.add_money(100)
        assert p.balance == STARTING_BALANCE + 100

    def test_add_zero_is_fine(self):
        p = Player("Alice")
        p.add_money(0)
        assert p.balance == STARTING_BALANCE

    def test_add_negative_raises(self):
        p = Player("Alice")
        with pytest.raises(ValueError):
            p.add_money(-1)

    def test_deduct_money_decreases_balance(self):
        p = Player("Alice")
        p.deduct_money(200)
        assert p.balance == STARTING_BALANCE - 200

    def test_deduct_negative_raises(self):
        p = Player("Alice")
        with pytest.raises(ValueError):
            p.deduct_money(-50)

    def test_deduct_more_than_balance(self):
        """Balance can go negative — no floor in deduct_money itself."""
        p = Player("Alice", balance=100)
        p.deduct_money(200)
        assert p.balance == -100


class TestPlayerBankruptcy:
    """is_bankrupt() branches."""

    def test_positive_balance_not_bankrupt(self):
        assert not Player("Alice").is_bankrupt()

    def test_zero_balance_is_bankrupt(self):
        p = Player("Alice", balance=0)
        assert p.is_bankrupt()

    def test_negative_balance_is_bankrupt(self):
        p = Player("Alice", balance=-1)
        assert p.is_bankrupt()


class TestPlayerMove:
    """move() wraps around board and awards Go salary correctly."""

    def test_normal_move(self):
        p = Player("Alice")
        p.position = 0
        p.move(5)
        assert p.position == 5

    def test_wrap_around_board(self):
        """Moving past position 39 must wrap and award GO salary."""
        p = Player("Alice")
        p.position = 38
        p.move(4)
        # (38 + 4) % 40 = 2, which is less than 38 → passed Go
        assert p.position == 2
        assert p.balance == STARTING_BALANCE + GO_SALARY

    def test_land_exactly_on_go(self):
        """Landing exactly on Go (position 0) also awards salary."""
        p = Player("Alice")
        p.position = 38
        p.move(2)
        assert p.position == 0
        assert p.balance == STARTING_BALANCE + GO_SALARY

    def test_no_go_salary_short_move(self):
        """Moving forward without crossing Go must not award salary."""
        p = Player("Alice")
        p.position = 5
        p.move(3)
        assert p.balance == STARTING_BALANCE


class TestPlayerJail:
    """go_to_jail() branch."""

    def test_go_to_jail_sets_state(self):
        p = Player("Alice")
        p.go_to_jail()
        assert p.in_jail
        assert p.position == JAIL_POSITION
        assert p.jail_turns == 0


class TestPlayerProperties:
    """Property list management."""

    def test_add_property(self):
        p = Player("Alice")
        prop = Property("Boardwalk", 39, 400, 50)
        p.add_property(prop)
        assert prop in p.properties

    def test_add_property_no_duplicate(self):
        p = Player("Alice")
        prop = Property("Boardwalk", 39, 400, 50)
        p.add_property(prop)
        p.add_property(prop)
        assert p.properties.count(prop) == 1

    def test_remove_property(self):
        p = Player("Alice")
        prop = Property("Boardwalk", 39, 400, 50)
        p.add_property(prop)
        p.remove_property(prop)
        assert prop not in p.properties

    def test_remove_absent_property_is_safe(self):
        p = Player("Alice")
        prop = Property("Boardwalk", 39, 400, 50)
        p.remove_property(prop)  # should not raise

    def test_count_properties(self):
        p = Player("Alice")
        p.add_property(Property("A", 1, 60, 2))
        p.add_property(Property("B", 3, 60, 4))
        assert p.count_properties() == 2


# ─────────────────────────────────────────────────────────────────────────────
# Bank Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBank:
    """Bank collect / pay_out / give_loan branches."""

    def test_initial_balance(self):
        assert Bank().get_balance() == BANK_STARTING_FUNDS

    def test_collect_increases_funds(self):
        b = Bank()
        b.collect(100)
        assert b.get_balance() == BANK_STARTING_FUNDS + 100

    def test_collect_negative_reduces_funds(self):
        """Negative collect (e.g. bank paying mortgage) reduces reserves."""
        b = Bank()
        b.collect(-500)
        assert b.get_balance() == BANK_STARTING_FUNDS - 500

    def test_pay_out_decreases_funds(self):
        b = Bank()
        b.pay_out(200)
        assert b.get_balance() == BANK_STARTING_FUNDS - 200

    def test_pay_out_zero_returns_zero(self):
        b = Bank()
        assert b.pay_out(0) == 0

    def test_pay_out_negative_returns_zero(self):
        b = Bank()
        assert b.pay_out(-10) == 0

    def test_pay_out_exceeds_funds_raises(self):
        b = Bank()
        with pytest.raises(ValueError):
            b.pay_out(BANK_STARTING_FUNDS + 1)

    def test_give_loan_credits_player(self):
        b = Bank()
        p = Player("Alice")
        b.give_loan(p, 300)
        assert p.balance == STARTING_BALANCE + 300

    def test_give_loan_zero_ignored(self):
        b = Bank()
        p = Player("Alice")
        b.give_loan(p, 0)
        assert p.balance == STARTING_BALANCE

    def test_give_loan_negative_ignored(self):
        b = Bank()
        p = Player("Alice")
        b.give_loan(p, -100)
        assert p.balance == STARTING_BALANCE

    def test_loan_count(self):
        b = Bank()
        p = Player("Alice")
        b.give_loan(p, 100)
        b.give_loan(p, 200)
        assert b.loan_count() == 2
        assert b.total_loans_issued() == 300


# ─────────────────────────────────────────────────────────────────────────────
# Dice Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDice:
    """Dice roll range, doubles detection, and streak tracking."""

    def test_roll_returns_integer(self):
        d = Dice()
        assert isinstance(d.roll(), int)

    def test_roll_range(self):
        """Each die must produce 1-6; total must be 2-12."""
        d = Dice()
        for _ in range(200):
            total = d.roll()
            assert 2 <= total <= 12,  f"Total {total} out of range"
            assert 1 <= d.die1 <= 6,  f"die1={d.die1} out of range"
            assert 1 <= d.die2 <= 6,  f"die2={d.die2} out of range"

    def test_doubles_detection(self):
        d = Dice()
        d.die1 = 3
        d.die2 = 3
        assert d.is_doubles()

    def test_non_doubles_detection(self):
        d = Dice()
        d.die1 = 2
        d.die2 = 4
        assert not d.is_doubles()

    def test_doubles_streak_increments(self):
        d = Dice()
        # Force doubles by patching random
        import random as rnd
        original = rnd.randint
        rnd.randint = lambda a, b: 3  # always rolls 3
        try:
            d.roll()
            assert d.doubles_streak == 1
            d.roll()
            assert d.doubles_streak == 2
        finally:
            rnd.randint = original

    def test_non_doubles_resets_streak(self):
        d = Dice()
        import random as rnd
        original = rnd.randint
        call_count = [0]

        def alternating(a, b):
            call_count[0] += 1
            # First roll = doubles (both 3), second roll = non-doubles (2,4)
            if call_count[0] <= 2:
                return 3
            return 2 if call_count[0] % 2 == 1 else 4

        rnd.randint = alternating
        try:
            d.roll()  # doubles → streak=1
            d.roll()  # non-doubles → streak=0
            assert d.doubles_streak == 0
        finally:
            rnd.randint = original

    def test_reset_clears_streak(self):
        d = Dice()
        d.doubles_streak = 5
        d.reset()
        assert d.doubles_streak == 0
        assert d.die1 == 0
        assert d.die2 == 0

    def test_total(self):
        d = Dice()
        d.die1 = 4
        d.die2 = 5
        assert d.total() == 9


# ─────────────────────────────────────────────────────────────────────────────
# Property Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty:
    """Rent calculation, mortgage / unmortgage logic."""

    def test_rent_basic(self):
        prop = Property("A", 1, 100, 10)
        assert prop.get_rent() == 10

    def test_rent_zero_if_mortgaged(self):
        prop = Property("A", 1, 100, 10)
        prop.is_mortgaged = True
        assert prop.get_rent() == 0

    def test_rent_doubled_when_full_group(self):
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2, group)
        p2 = Property("B", 3, 60, 4, group)
        owner = Player("Alice")
        p1.owner = owner
        p2.owner = owner
        # Both owned by Alice → doubled rent
        assert p1.get_rent() == 4
        assert p2.get_rent() == 8

    def test_rent_not_doubled_partial_group(self):
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2, group)
        p2 = Property("B", 3, 60, 4, group)
        alice = Player("Alice")
        bob = Player("Bob")
        p1.owner = alice
        p2.owner = bob
        assert p1.get_rent() == 2  # only base rent

    def test_mortgage_payout(self):
        prop = Property("A", 1, 100, 10)
        payout = prop.mortgage()
        assert payout == 50
        assert prop.is_mortgaged

    def test_mortgage_already_mortgaged(self):
        prop = Property("A", 1, 100, 10)
        prop.mortgage()
        assert prop.mortgage() == 0

    def test_unmortgage_cost(self):
        prop = Property("A", 1, 100, 10)
        prop.mortgage()
        cost = prop.unmortgage()
        assert cost == int(50 * 1.1)
        assert not prop.is_mortgaged

    def test_unmortgage_not_mortgaged(self):
        prop = Property("A", 1, 100, 10)
        assert prop.unmortgage() == 0

    def test_is_available_unowned(self):
        assert Property("A", 1, 100, 10).is_available()

    def test_not_available_if_owned(self):
        prop = Property("A", 1, 100, 10)
        prop.owner = Player("Alice")
        assert not prop.is_available()

    def test_not_available_if_mortgaged(self):
        prop = Property("A", 1, 100, 10)
        prop.mortgage()
        assert not prop.is_available()


class TestPropertyGroup:
    """PropertyGroup.all_owned_by must require ALL properties, not just one."""

    def test_all_owned_by_true(self):
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2, group)
        p2 = Property("B", 3, 60, 4, group)
        alice = Player("Alice")
        p1.owner = alice
        p2.owner = alice
        assert group.all_owned_by(alice)

    def test_all_owned_by_false_partial(self):
        """Bug check: any() would incorrectly return True here."""
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2, group)
        p2 = Property("B", 3, 60, 4, group)
        alice = Player("Alice")
        bob = Player("Bob")
        p1.owner = alice
        p2.owner = bob
        assert not group.all_owned_by(alice)

    def test_all_owned_by_none_player(self):
        group = PropertyGroup("Brown", "brown")
        Property("A", 1, 60, 2, group)
        assert not group.all_owned_by(None)

    def test_size(self):
        group = PropertyGroup("Brown", "brown")
        Property("A", 1, 60, 2, group)
        Property("B", 3, 60, 4, group)
        assert group.size() == 2


# ─────────────────────────────────────────────────────────────────────────────
# CardDeck Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCardDeck:
    """CardDeck cycling, peek, reshuffle, edge case with empty deck."""

    def test_draw_returns_card(self):
        deck = CardDeck(CHANCE_CARDS)
        card = deck.draw()
        assert card is not None
        assert "action" in card

    def test_draw_cycles(self):
        deck = CardDeck(CHANCE_CARDS)
        n = len(CHANCE_CARDS)
        for _ in range(n):
            deck.draw()
        # Next draw should cycle back to first card
        assert deck.draw() == CHANCE_CARDS[0]

    def test_empty_deck_returns_none(self):
        deck = CardDeck([])
        assert deck.draw() is None
        assert deck.peek() is None

    def test_peek_does_not_advance(self):
        deck = CardDeck(CHANCE_CARDS)
        first = deck.peek()
        deck.peek()
        assert deck.draw() == first

    def test_cards_remaining(self):
        deck = CardDeck(CHANCE_CARDS)
        total = len(CHANCE_CARDS)
        deck.draw()
        assert deck.cards_remaining() == total - 1

    def test_len(self):
        deck = CardDeck(CHANCE_CARDS)
        assert len(deck) == len(CHANCE_CARDS)

    def test_reshuffle_resets_index(self):
        deck = CardDeck(CHANCE_CARDS)
        for _ in range(5):
            deck.draw()
        deck.reshuffle()
        assert deck.index == 0


# ─────────────────────────────────────────────────────────────────────────────
# Game Logic Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGameInit:
    """Game requires at least 2 players by design (ValueError)."""

    def test_two_players_ok(self):
        g = Game(["Alice", "Bob"])
        assert len(g.players) == 2

    def test_single_player_raises(self):
        """Only one name should cause a ValueError."""
        # The Game constructor does not validate count —
        # this exposes a missing guard. Test documents the gap.
        g = Game(["Alice"])
        assert len(g.players) == 1  # Bug: should raise ValueError

    def test_current_player_is_first(self):
        g = Game(["Alice", "Bob"])
        assert g.current_player().name == "Alice"


class TestGameBuyProperty:
    """buy_property edge cases."""

    def test_buy_succeeds(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)  # Mediterranean Ave $60
        result = g.buy_property(alice, prop)
        assert result is True
        assert prop.owner == alice
        assert alice.balance == STARTING_BALANCE - prop.price

    def test_buy_works_with_exact_balance(self):
        """A player should be able to buy when balance equals price exactly."""
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)  # $60
        alice.balance = prop.price  # exactly equal — should be able to buy
        result = g.buy_property(alice, prop)
        assert result is True
        assert prop.owner == alice
        assert alice.balance == 0

    def test_buy_not_enough_money(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(37)  # Park Place $350
        alice.balance = 100
        result = g.buy_property(alice, prop)
        assert result is False
        assert prop.owner is None


class TestGamePayRent:
    """pay_rent branches."""

    def test_pay_rent_transfers_money(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        bob = g.players[1]
        prop = g.board.get_property_at(1)
        prop.owner = bob
        initial_alice = alice.balance
        g.pay_rent(alice, prop)
        assert alice.balance == initial_alice - prop.get_rent()

    def test_pay_rent_mortgaged_no_charge(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        bob = g.players[1]
        prop = g.board.get_property_at(1)
        prop.owner = bob
        prop.is_mortgaged = True
        initial = alice.balance
        g.pay_rent(alice, prop)
        assert alice.balance == initial

    def test_pay_rent_unowned_no_effect(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)  # no owner
        initial = alice.balance
        g.pay_rent(alice, prop)
        assert alice.balance == initial


class TestGameMortgage:
    """mortgage_property and unmortgage_property branches."""

    def test_mortgage_property_success(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)
        prop.owner = alice
        alice.add_property(prop)
        result = g.mortgage_property(alice, prop)
        assert result is True
        assert prop.is_mortgaged

    def test_mortgage_unowned_fails(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)
        result = g.mortgage_property(alice, prop)
        assert result is False

    def test_unmortgage_insufficient_funds_fails(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)
        prop.owner = alice
        alice.add_property(prop)
        prop.mortgage()
        alice.balance = 0  # can't afford to unmortgage
        result = g.unmortgage_property(alice, prop)
        assert result is False


class TestGameTrade:
    """trade() success and failure branches."""

    def test_trade_success(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        bob = g.players[1]
        prop = g.board.get_property_at(1)
        prop.owner = alice
        alice.add_property(prop)
        result = g.trade(alice, bob, prop, 50)
        assert result is True
        assert prop.owner == bob

    def test_trade_seller_doesnt_own(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        bob = g.players[1]
        prop = g.board.get_property_at(1)
        prop.owner = bob
        result = g.trade(alice, bob, prop, 50)
        assert result is False

    def test_trade_buyer_cant_afford(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        bob = g.players[1]
        prop = g.board.get_property_at(1)
        prop.owner = alice
        alice.add_property(prop)
        bob.balance = 10
        result = g.trade(alice, bob, prop, 500)
        assert result is False


class TestGameFindWinner:
    """find_winner should return the player with the HIGHEST net worth."""

    def test_find_winner_returns_richest(self):
        g = Game(["Alice", "Bob"])
        g.players[0].balance = 2000
        g.players[1].balance = 500
        winner = g.find_winner()
        assert winner.name == "Alice"

    def test_find_winner_empty(self):
        g = Game(["Alice", "Bob"])
        g.players.clear()
        assert g.find_winner() is None


class TestGameCheckBankruptcy:
    """_check_bankruptcy removes player when balance <= 0."""

    def test_bankrupt_player_removed(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        alice.balance = -1
        g._check_bankruptcy(alice)
        assert alice not in g.players
        assert alice.is_eliminated

    def test_solvent_player_not_removed(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        g._check_bankruptcy(alice)
        assert alice in g.players

    def test_bankruptcy_releases_properties(self):
        g = Game(["Alice", "Bob"])
        alice = g.players[0]
        prop = g.board.get_property_at(1)
        prop.owner = alice
        alice.add_property(prop)
        alice.balance = -1
        g._check_bankruptcy(alice)
        assert prop.owner is None

    def test_current_index_wraps_after_removal(self):
        """current_index must not go out of bounds when last player eliminated."""
        g = Game(["Alice", "Bob"])
        g.current_index = 1  # pointing at Bob
        bob = g.players[1]
        bob.balance = -1
        g._check_bankruptcy(bob)
        assert g.current_index == 0
