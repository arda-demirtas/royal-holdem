from evaluator import Card, evaluate_7_card_hand

def run_tests():
    # 1. Royal Flush
    cards = [
        Card('A', 'h'), Card('K', 'h'), Card('Q', 'h'), Card('J', 'h'), Card('10', 'h'),
        Card('2', 'c'), Card('3', 'd')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Royal Flush. Got: {name} (value={val}, tie={tie})")
    assert name == "Royal Flush"
    assert val == 9

    # 2. Straight Flush
    cards = [
        Card('9', 's'), Card('8', 's'), Card('7', 's'), Card('6', 's'), Card('5', 's'),
        Card('2', 'c'), Card('A', 'd')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Straight Flush. Got: {name} (value={val}, tie={tie})")
    assert name == "Straight Flush"
    assert val == 8

    # 3. Four of a Kind
    cards = [
        Card('J', 'h'), Card('J', 'd'), Card('J', 's'), Card('J', 'c'), Card('K', 'h'),
        Card('K', 'd'), Card('3', 'c')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Four of a Kind. Got: {name} (value={val}, tie={tie})")
    assert name == "Four of a Kind"
    assert val == 7

    # 4. Full House
    cards = [
        Card('10', 'h'), Card('10', 'd'), Card('10', 's'), Card('4', 'h'), Card('4', 'd'),
        Card('A', 'c'), Card('2', 's')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Full House. Got: {name} (value={val}, tie={tie})")
    assert name == "Full House"
    assert val == 6

    # 5. Flush
    cards = [
        Card('A', 'c'), Card('10', 'c'), Card('7', 'c'), Card('5', 'c'), Card('2', 'c'),
        Card('K', 'h'), Card('Q', 'd')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Flush. Got: {name} (value={val}, tie={tie})")
    assert name == "Flush"
    assert val == 5

    # 6. Straight
    cards = [
        Card('8', 'h'), Card('7', 'd'), Card('6', 's'), Card('5', 'c'), Card('4', 'h'),
        Card('2', 'c'), Card('A', 'd')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Straight. Got: {name} (value={val}, tie={tie})")
    assert name == "Straight"
    assert val == 4

    # 7. Three of a Kind
    cards = [
        Card('Q', 'h'), Card('Q', 'd'), Card('Q', 's'), Card('A', 'c'), Card('K', 'h'),
        Card('2', 'd'), Card('3', 'c')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Three of a Kind. Got: {name} (value={val}, tie={tie})")
    assert name == "Three of a Kind"
    assert val == 3

    # 8. Two Pair
    cards = [
        Card('J', 'h'), Card('J', 'd'), Card('9', 's'), Card('9', 'c'), Card('A', 'h'),
        Card('2', 'd'), Card('3', 'c')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: Two Pair. Got: {name} (value={val}, tie={tie})")
    assert name == "Two Pair"
    assert val == 2

    # 9. One Pair
    cards = [
        Card('A', 'h'), Card('A', 'd'), Card('K', 's'), Card('Q', 'c'), Card('J', 'h'),
        Card('2', 'd'), Card('3', 'c')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: One Pair. Got: {name} (value={val}, tie={tie})")
    assert name == "One Pair"
    assert val == 1

    # 10. High Card
    cards = [
        Card('A', 'h'), Card('K', 'd'), Card('J', 's'), Card('9', 'c'), Card('7', 'h'),
        Card('5', 'd'), Card('2', 'c')
    ]
    val, tie, name = evaluate_7_card_hand(cards)
    print(f"Expected: High Card. Got: {name} (value={val}, tie={tie})")
    assert name == "High Card"
    assert val == 0

    print("ALL TESTS PASSED!")

if __name__ == '__main__':
    run_tests()
