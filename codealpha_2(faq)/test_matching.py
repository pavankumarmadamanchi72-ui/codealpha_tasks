import sys
from nlp_engine import FAQBot

def test():
    print("Initializing FAQBot...")
    bot = FAQBot('faq_data.json')
    
    test_cases = [
        # Direct questions
        ("How do I set up my Aura Smart Home Hub for the first time?", True, 1),
        # Paraphrased questions
        ("setup the aura hub first time", True, 1),
        ("led status lights meaning?", True, 2),
        ("Does it support 5GHz wifi?", True, 4),
        ("Can I use Apple HomeKit with it?", True, 7),
        ("Is there a monthly fee?", True, 10),
        ("factory reset guide", True, 11),
        # Unrelated questions that should have low similarity or fail threshold
        ("what is the weather today?", False, None),
        ("how to bake chocolate cookies", False, None)
    ]
    
    passed = 0
    for query, expected_match, expected_id in test_cases:
        match, score = bot.find_match(query)
        match_id = match['id'] if match else None
        
        if expected_match:
            if match and match_id == expected_id:
                print(f"PASS: Query '{query}' -> matched ID {match_id} (Score: {score:.2f})")
                passed += 1
            else:
                print(f"FAIL: Query '{query}' -> expected match ID {expected_id}, but got match {match_id} (Score: {score:.2f})")
        else:
            if match is None:
                print(f"PASS: Query '{query}' -> no match found as expected (Score: {score:.2f})")
                passed += 1
            else:
                print(f"FAIL: Query '{query}' -> expected no match, but matched ID {match_id} (Score: {score:.2f})")
                
    print(f"\nTests completed. {passed}/{len(test_cases)} passed.")
    if passed == len(test_cases):
        print("All matching checks passed successfully!")
        sys.exit(0)
    else:
        print("Some matching checks failed.")
        sys.exit(1)

if __name__ == '__main__':
    test()
