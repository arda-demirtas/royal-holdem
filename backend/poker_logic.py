import random
from typing import List, Dict, Optional, Tuple
from evaluator import Card, evaluate_7_card_hand, HAND_NAMES

class Deck:
    def __init__(self):
        suits = ['h', 'd', 'c', 's']  # Hearts, Diamonds, Clubs, Spades
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = [Card(r, s) for r in ranks for s in suits]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if not self.cards:
            raise ValueError("Deck is empty")
        return self.cards.pop()

class Player:
    def __init__(self, user_id: int, username: str, chips: int, seat_index: int, avatar_id: int = 1, bankroll_chips: int = 100000):
        self.user_id = user_id
        self.username = username
        self.chips = chips  # Chips in this tournament
        self.avatar_id = avatar_id
        self.bankroll_chips = bankroll_chips
        self.cards: List[Card] = []
        self.is_folded = False
        self.is_all_in = False
        self.current_bet = 0  # Bet in the current round
        self.chips_in_pot = 0  # Total chips contributed in the current hand
        self.is_connected = True
        self.seat_index = seat_index
        self.last_action: Optional[str] = None
        self.hand_description: Optional[str] = None

    def reset_for_hand(self):
        self.cards = []
        self.is_folded = False
        self.is_all_in = False
        self.current_bet = 0
        self.chips_in_pot = 0
        self.last_action = None
        self.hand_description = None

    def reset_for_round(self):
        self.current_bet = 0
        self.last_action = None

    def to_dict(self, reveal_cards: bool = False):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "chips": self.chips,
            "avatar_id": self.avatar_id,
            "bankroll_chips": self.bankroll_chips,
            "cards": [c.to_dict() for c in self.cards] if reveal_cards or self.is_folded else [{"rank": "?", "suit": "?"} for _ in self.cards],
            "is_folded": self.is_folded,
            "is_all_in": self.is_all_in,
            "current_bet": self.current_bet,
            "chips_in_pot": self.chips_in_pot,
            "is_connected": self.is_connected,
            "seat_index": self.seat_index,
            "last_action": self.last_action,
            "hand_description": self.hand_description if reveal_cards else None
        }

BLIND_LEVELS = [
    (20, 40),
    (30, 60),
    (50, 100),
    (100, 200),
    (200, 400),
    (300, 600),
    (500, 1000),
    (1000, 2000)
]

class PokerGame:
    def __init__(self, tournament_id: str, players: List[Player]):
        self.tournament_id = tournament_id
        self.players = players  # List of Player objects
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.betting_round = "waiting"  # pre-flop, flop, turn, river, showdown, finished
        self.current_bet = 0  # Highest bet in current round
        self.last_raise = 0  # Last raise amount (used to calculate min raise)
        self.dealer_index = 0
        self.current_turn_index = -1
        self.small_blind = 20
        self.big_blind = 40
        self.blind_level_index = 0
        self.hand_count = 0
        self.game_log: List[str] = []
        self.winner_id: Optional[int] = None
        self.action_history: Dict[int, bool] = {}  # Tracks if a player acted in this round

    def log(self, message: str):
        self.game_log.append(message)
        if len(self.game_log) > 40:
            self.game_log.pop(0)

    def start_game(self):
        self.log("Tournament started!")
        self.dealer_index = random.randint(0, len(self.players) - 1)
        self.start_new_hand()

    def start_new_hand(self):
        self.hand_count += 1
        # Update blinds every 5 hands
        self.blind_level_index = min((self.hand_count - 1) // 5, len(BLIND_LEVELS) - 1)
        self.small_blind, self.big_blind = BLIND_LEVELS[self.blind_level_index]

        self.log(f"--- Hand #{self.hand_count} (Blinds: {self.small_blind}/{self.big_blind}) ---")

        # Reset players
        for p in self.players:
            if p.chips > 0:
                p.reset_for_hand()
            else:
                p.is_folded = True  # Out of the game

        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.last_raise = self.big_blind

        # Check if tournament is finished (only one player has chips)
        active_players = [p for p in self.players if p.chips > 0]
        if len(active_players) <= 1:
            self.betting_round = "finished"
            self.winner_id = active_players[0].user_id if active_players else None
            winner_name = active_players[0].username if active_players else "Unknown"
            self.log(f"Tournament Finished! Winner: {winner_name}")
            return

        # Move dealer button
        while True:
            self.dealer_index = (self.dealer_index + 1) % len(self.players)
            if self.players[self.dealer_index].chips > 0:
                break

        # Deal pocket cards
        for _ in range(2):
            for p in self.players:
                if not p.is_folded:
                    p.cards.append(self.deck.deal())

        self.betting_round = "pre-flop"
        self.post_blinds()
        self.action_history = {}
        self.start_betting_round()

    def post_blinds(self):
        n = len(self.players)
        # Find small blind player
        sb_index = (self.dealer_index + 1) % n
        while self.players[sb_index].chips == 0:
            sb_index = (sb_index + 1) % n

        # Find big blind player
        bb_index = (sb_index + 1) % n
        while self.players[bb_index].chips == 0:
            bb_index = (bb_index + 1) % n

        # Post SB
        sb_player = self.players[sb_index]
        sb_posted = min(sb_player.chips, self.small_blind)
        sb_player.chips -= sb_posted
        sb_player.current_bet = sb_posted
        sb_player.chips_in_pot = sb_posted
        if sb_player.chips == 0:
            sb_player.is_all_in = True
        self.log(f"{sb_player.username} posts small blind {sb_posted}")

        # Post BB
        bb_player = self.players[bb_index]
        bb_posted = min(bb_player.chips, self.big_blind)
        bb_player.chips -= bb_posted
        bb_player.current_bet = bb_posted
        bb_player.chips_in_pot = bb_posted
        if bb_player.chips == 0:
            bb_player.is_all_in = True
        self.log(f"{bb_player.username} posts big blind {bb_posted}")

        self.current_bet = bb_posted
        self.pot = sb_posted + bb_posted

        # Pre-flop action starts next to Big Blind
        self.current_turn_index = (bb_index + 1) % n
        while self.players[self.current_turn_index].is_folded or self.players[self.current_turn_index].is_all_in:
            self.current_turn_index = (self.current_turn_index + 1) % n

    def start_betting_round(self):
        # Reset current bets for players
        for p in self.players:
            p.reset_for_round()
        self.action_history = {}

        if self.betting_round == "pre-flop":
            # Blinds were already posted, so current_bet is Big Blind.
            # We don't reset current_bet or pot.
            # Note: sb and bb current_bet are already set in post_blinds, so we must restore them
            n = len(self.players)
            sb_index = (self.dealer_index + 1) % n
            while self.players[sb_index].is_folded:
                sb_index = (sb_index + 1) % n
            bb_index = (sb_index + 1) % n
            while self.players[bb_index].is_folded:
                bb_index = (bb_index + 1) % n

            self.players[sb_index].current_bet = min(self.small_blind, self.players[sb_index].chips_in_pot)
            self.players[bb_index].current_bet = min(self.big_blind, self.players[bb_index].chips_in_pot)
            self.current_bet = max(p.current_bet for p in self.players)
            self.last_raise = self.big_blind
        else:
            self.current_bet = 0
            self.last_raise = self.big_blind
            # Action starts left of dealer
            self.current_turn_index = (self.dealer_index + 1) % len(self.players)
            self.find_next_active_player()

        self.check_betting_round_finished()

    def find_next_active_player(self):
        start = self.current_turn_index
        n = len(self.players)
        while True:
            p = self.players[self.current_turn_index]
            if not p.is_folded and not p.is_all_in and p.chips > 0:
                break
            self.current_turn_index = (self.current_turn_index + 1) % n
            if self.current_turn_index == start:
                break

    def get_min_raise(self) -> int:
        # Minimum raise is current_bet + last_raise
        # If no bets have been made, min bet/raise is 1 Big Blind
        if self.current_bet == 0:
            return self.big_blind
        return self.current_bet + self.last_raise

    def process_action(self, user_id: int, action: str, amount: int = 0) -> bool:
        """
        Process a player action.
        action can be: 'fold', 'check', 'call', 'raise'
        """
        if self.betting_round in ["showdown", "finished", "waiting"]:
            return False

        active_player = self.players[self.current_turn_index]
        if active_player.user_id != user_id:
            return False  # Not this player's turn

        action = action.lower()
        if action == "fold":
            active_player.is_folded = True
            active_player.last_action = "Fold"
            self.log(f"{active_player.username} folds")

        elif action == "check":
            # Check only allowed if current player bet matches the highest bet
            if active_player.current_bet != self.current_bet:
                return False
            active_player.last_action = "Check"
            self.log(f"{active_player.username} checks")

        elif action == "call":
            call_amount = self.current_bet - active_player.current_bet
            if call_amount <= 0:
                # Treated as a check
                active_player.last_action = "Check"
                self.log(f"{active_player.username} checks (call 0)")
            else:
                actual_call = min(active_player.chips, call_amount)
                active_player.chips -= actual_call
                active_player.current_bet += actual_call
                active_player.chips_in_pot += actual_call
                self.pot += actual_call
                if active_player.chips == 0:
                    active_player.is_all_in = True
                    active_player.last_action = f"Call (All-in {actual_call})"
                    self.log(f"{active_player.username} calls {actual_call} and is ALL-IN!")
                else:
                    active_player.last_action = f"Call {actual_call}"
                    self.log(f"{active_player.username} calls {actual_call}")

        elif action == "raise":
            # To raise, the player must bet an amount total in this round
            # e.g., if current_bet is 200, and they raise to 500, amount is 500.
            # The additional chips they need to add is amount - current_bet_of_player.
            min_raise = self.get_min_raise()
            
            # If the player is raising all-in for less than min_raise, it is allowed
            is_all_in_raise = (amount >= active_player.chips + active_player.current_bet)
            
            if amount < min_raise and not is_all_in_raise:
                # If they try to raise less than min raise, clamp to min raise if they have it
                amount = min_raise
                if amount > active_player.chips + active_player.current_bet:
                    amount = active_player.chips + active_player.current_bet

            added_chips = amount - active_player.current_bet
            if added_chips <= 0 or added_chips > active_player.chips:
                return False  # Invalid chips amount

            # Track raise size
            raise_diff = amount - self.current_bet
            if raise_diff > 0:
                self.last_raise = raise_diff

            active_player.chips -= added_chips
            active_player.current_bet = amount
            active_player.chips_in_pot += added_chips
            self.pot += added_chips
            self.current_bet = amount

            if active_player.chips == 0:
                active_player.is_all_in = True
                active_player.last_action = f"Raise to {amount} (All-in)"
                self.log(f"{active_player.username} raises to {amount} (ALL-IN)")
            else:
                active_player.last_action = f"Raise to {amount}"
                self.log(f"{active_player.username} raises to {amount}")

        else:
            return False

        # Mark that the player has acted
        self.action_history[active_player.user_id] = True

        # Check if the betting round is finished
        if not self.check_betting_round_finished():
            # Move to next player
            self.advance_turn()

        return True

    def advance_turn(self):
        n = len(self.players)
        self.current_turn_index = (self.current_turn_index + 1) % n
        self.find_next_active_player()

    def check_betting_round_finished(self) -> bool:
        # A betting round is finished if:
        # 1. Only 1 active player is left (others folded).
        # 2. All active non-all-in players have matched the current_bet AND have acted.

        active_players = [p for p in self.players if not p.is_folded]
        
        # Scenario 1: Only 1 active player remains
        if len(active_players) <= 1:
            self.end_hand_by_folds()
            return True

        # Scenario 2: All players except one (or all) are all-in or folded
        non_all_in_active = [p for p in active_players if not p.is_all_in]
        if len(non_all_in_active) <= 1:
            # No further betting is possible.
            # Reveal cards and deal remaining community cards
            self.run_to_showdown()
            return True

        # Check if all active non-all-in players have acted and match the current bet
        for p in non_all_in_active:
            if not self.action_history.get(p.user_id, False) or p.current_bet != self.current_bet:
                return False

        # If we reach here, the betting round is complete
        self.transition_to_next_round()
        return True

    def transition_to_next_round(self):
        if self.betting_round == "pre-flop":
            self.betting_round = "flop"
            # Deal 3 cards
            for _ in range(3):
                self.community_cards.append(self.deck.deal())
            self.log(f"Flop dealt: {' '.join(repr(c) for c in self.community_cards)}")
            self.start_betting_round()

        elif self.betting_round == "flop":
            self.betting_round = "turn"
            # Deal 1 card
            self.community_cards.append(self.deck.deal())
            self.log(f"Turn dealt: {self.community_cards[-1]}")
            self.start_betting_round()

        elif self.betting_round == "turn":
            self.betting_round = "river"
            # Deal 1 card
            self.community_cards.append(self.deck.deal())
            self.log(f"River dealt: {self.community_cards[-1]}")
            self.start_betting_round()

        elif self.betting_round == "river":
            self.betting_round = "showdown"
            self.showdown()

    def run_to_showdown(self):
        # Deal remaining community cards
        cards_needed = 5 - len(self.community_cards)
        if cards_needed > 0:
            for _ in range(cards_needed):
                self.community_cards.append(self.deck.deal())
            self.log(f"Dealing community cards: {' '.join(repr(c) for c in self.community_cards)}")

        self.betting_round = "showdown"
        self.showdown()

    def end_hand_by_folds(self):
        # Find the single active player left
        winner = [p for p in self.players if not p.is_folded][0]
        winner.chips += self.pot
        self.log(f"{winner.username} wins pot of {self.pot} (all others folded)")
        self.pot = 0
        self.betting_round = "showdown"
        # We wait briefly and start a new hand

    def showdown(self):
        # We need to evaluate hands for all active players
        active_players = [p for p in self.players if not p.is_folded]
        
        if len(active_players) == 0:
            # Edge case
            self.pot = 0
            self.start_new_hand()
            return

        if len(active_players) == 1:
            # Hand ended by folds earlier, already handled, but safeguard:
            winner = active_players[0]
            winner.chips += self.pot
            self.pot = 0
            return

        # Evaluate hands
        evaluations = []
        for p in active_players:
            # 7 cards = 2 pocket + 5 community
            all_cards = p.cards + self.community_cards
            val, tie_breakers, name = evaluate_7_card_hand(all_cards)
            p.hand_description = name
            evaluations.append((p, (val, tie_breakers)))
            self.log(f"{p.username} shows {p.cards[0]}{p.cards[1]} -> {name}")

        # Sort evaluations by hand strength descending
        evaluations.sort(key=lambda x: x[1], reverse=True)

        # Showdown Pot Distribution Algorithm (Side pots support)
        # Each player O has p.chips_in_pot contributed.
        # We iterate through winning players from best to worst hand.
        # Tie groups must be processed together so they split correctly.
        
        # Group evaluations by strength
        strength_groups: List[List[Tuple[Player, Tuple[int, List[int]]]]] = []
        for item in evaluations:
            player, strength = item
            if not strength_groups:
                strength_groups.append([item])
            else:
                # Compare strength tuples
                if strength == strength_groups[-1][0][1]:
                    strength_groups[-1].append(item)
                else:
                    strength_groups.append([item])

        # Distribute chips
        for group in strength_groups:
            # Players in this group tie
            # They split the pot they are eligible for.
            # To find the eligible amount, for each player in group, they can take up to their chips_in_pot contribution from every other player.
            # Let's do it round-by-round or directly:
            # While there are chips in the pot contributed by anyone:
            # Each winner in the group can win chips up to their chips_in_pot from any other player's contribution.
            
            # Find the max contribution of a player in this group that has not been claimed yet.
            # To do this safely:
            # For each player in the group, we calculate what they can win.
            # Since they tie, we must do it collectively.
            
            # A tie group will split the minimum contributions.
            # Let's say group has P1 (contributed 300) and P2 (contributed 500).
            # The maximum they can claim in common is min(contribution).
            # Let's sort group players by their chips_in_pot ascending.
            group.sort(key=lambda x: x[0].chips_in_pot)
            
            for idx, (p_winner, _) in enumerate(group):
                win_limit = p_winner.chips_in_pot
                if win_limit == 0:
                    continue
                
                # Number of players in the group who are eligible for at least this amount
                active_winners_count = len(group) - idx
                
                # Collect from all players at the table (active or folded)
                total_collected = 0
                collected_details = {}
                
                for p_other in self.players:
                    take_amount = min(p_other.chips_in_pot, win_limit)
                    if take_amount > 0:
                        collected_details[p_other.user_id] = take_amount
                
                # Split this collected amount among the active winners in the group
                for p_win_sub, _ in group[idx:]:
                    # Each of the remaining winners splits the collected amounts
                    sub_win = 0
                    for uid, amt in list(collected_details.items()):
                        share = amt / active_winners_count
                        sub_win += share
                    p_win_sub.chips += int(sub_win)
                    
                # Deduct the collected amounts from all players' contributions
                for p_other in self.players:
                    take_amount = min(p_other.chips_in_pot, win_limit)
                    p_other.chips_in_pot -= take_amount

                # Subtract from win_limit of the remaining winners
                for p_win_sub, _ in group[idx + 1:]:
                    p_win_sub.chips_in_pot -= win_limit
                
                p_winner.chips_in_pot = 0

        # Any remaining dust goes to the player with the absolute best hand (first in sorted list)
        total_remaining = sum(p.chips_in_pot for p in self.players)
        if total_remaining > 0:
            evaluations[0][0].chips += total_remaining
            for p in self.players:
                p.chips_in_pot = 0
        
        self.pot = sum(p.chips_in_pot for p in self.players)
        
        # Log winners
        # Find who won chips in this hand
        # We can write a log line for each player whose chip stack increased
        # To do this, we'll keep track of their chips before and after if needed, but a simple log works:
        # "Showdown complete. Next hand starting shortly."
        self.log("Showdown complete. Hand ended.")

    def to_dict(self, current_user_id: Optional[int] = None):
        return {
            "tournament_id": self.tournament_id,
            "players": [p.to_dict(reveal_cards=(self.betting_round == "showdown" or p.user_id == current_user_id)) for p in self.players],
            "community_cards": [c.to_dict() for c in self.community_cards],
            "pot": self.pot,
            "betting_round": self.betting_round,
            "current_bet": self.current_bet,
            "min_raise": self.get_min_raise(),
            "dealer_index": self.dealer_index,
            "current_turn_index": self.current_turn_index,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "hand_count": self.hand_count,
            "game_log": self.game_log,
            "winner_id": self.winner_id
        }
