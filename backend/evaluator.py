import itertools
from typing import List, Tuple, Dict

# Map card ranks to values
RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}
VALUE_TO_RANK = {v: k for k, v in RANK_VALUES.items()}

HAND_NAMES = {
    9: "Royal Flush",
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card"
}

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self):
        return {"rank": self.rank, "suit": self.suit}

    @classmethod
    def from_str(cls, card_str: str):
        # Handles "10s", "Ah", etc.
        if card_str.startswith("10"):
            return cls("10", card_str[2])
        return cls(card_str[0], card_str[1])

def evaluate_5_card_hand(cards: List[Card]) -> Tuple[int, List[int], str]:
    """
    Evaluates a 5 card hand.
    Returns: (category_value, tie_breaker_values, hand_name)
    """
    values = sorted([c.value for c in cards], reverse=True)
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1

    # Check for straight
    is_straight = False
    straight_high = 0

    # Normal straight check
    unique_values = sorted(list(set(values)), reverse=True)
    if len(unique_values) == 5:
        if unique_values[0] - unique_values[4] == 4:
            is_straight = True
            straight_high = unique_values[0]
        # Ace-low straight check (A, 5, 4, 3, 2)
        elif unique_values == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    # Group values to find pairs, trips, quads
    value_counts: Dict[int, int] = {}
    for v in values:
        value_counts[v] = value_counts.get(v, 0) + 1

    count_groups = {}
    for v, count in value_counts.items():
        count_groups.setdefault(count, []).append(v)
    for count in count_groups:
        count_groups[count].sort(reverse=True)

    # 1. Royal Flush and Straight Flush
    if is_flush and is_straight:
        if straight_high == 14:
            return 9, [14], "Royal Flush"
        return 8, [straight_high], "Straight Flush"

    # 2. Four of a Kind
    if 4 in count_groups:
        quad_rank = count_groups[4][0]
        kicker = count_groups[1][0]
        return 7, [quad_rank, kicker], "Four of a Kind"

    # 3. Full House
    if 3 in count_groups and 2 in count_groups:
        trips_rank = count_groups[3][0]
        pair_rank = count_groups[2][0]
        return 6, [trips_rank, pair_rank], "Full House"
    elif 3 in count_groups and len(count_groups[3]) > 1:
        # Special case: Two sets of trips (e.g. 3 Aces and 3 Kings). One pair is formed by the lower trips.
        trips_rank = count_groups[3][0]
        pair_rank = count_groups[3][1]
        return 6, [trips_rank, pair_rank], "Full House"

    # 4. Flush
    if is_flush:
        return 5, values, "Flush"

    # 5. Straight
    if is_straight:
        return 4, [straight_high], "Straight"

    # 6. Three of a Kind
    if 3 in count_groups:
        trips_rank = count_groups[3][0]
        kickers = count_groups[1]
        return 3, [trips_rank] + kickers, "Three of a Kind"

    # 7. Two Pair
    if 2 in count_groups and len(count_groups[2]) >= 2:
        high_pair = count_groups[2][0]
        low_pair = count_groups[2][1]
        # Remaining cards are kickers
        kickers = [v for v in values if v != high_pair and v != low_pair]
        return 2, [high_pair, low_pair, kickers[0]], "Two Pair"

    # 8. One Pair
    if 2 in count_groups:
        pair_rank = count_groups[2][0]
        kickers = count_groups[1]
        return 1, [pair_rank] + kickers, "One Pair"

    # 9. High Card
    return 0, values, "High Card"

def evaluate_7_card_hand(cards: List[Card]) -> Tuple[int, List[int], str]:
    """
    Finds the best 5-card hand from a list of 7 cards.
    Returns: (category_value, tie_breaker_values, hand_name)
    """
    best_rank = (-1, [])
    best_name = "High Card"

    for combo in itertools.combinations(cards, 5):
        cat_val, tie_breakers, name = evaluate_5_card_hand(list(combo))
        # Direct comparison of tuple (cat_val, tie_breakers)
        if (cat_val, tie_breakers) > best_rank:
            best_rank = (cat_val, tie_breakers)
            best_name = name

    return best_rank[0], best_rank[1], best_name
