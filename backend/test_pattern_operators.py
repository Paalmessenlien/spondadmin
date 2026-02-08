#!/usr/bin/env python3
"""
Test script for pattern matching with AND/OR operators
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.category_service import CategoryService


def test_pattern_matching():
    """Test pattern matching with various operator combinations"""

    print("=" * 60)
    print("Testing Pattern Matching with AND/OR Operators")
    print("=" * 60)

    # Test Case 1: OR logic (default behavior)
    print("\nTest Case 1: OR Logic")
    print("-" * 60)
    test_text = "Fabrikken training"
    patterns_or = [
        {"type": "contains", "value": "Fabrikken", "case_insensitive": True},
        {"type": "contains", "value": "Barn", "case_insensitive": True, "operator": "OR"}
    ]

    # Evaluate first pattern
    result = CategoryService._match_pattern(test_text, patterns_or[0])
    print(f"Pattern 1 matches '{test_text}': {result}")

    # Evaluate second pattern with OR
    for i in range(1, len(patterns_or)):
        pattern = patterns_or[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        print(f"Pattern 2 matches '{test_text}': {pattern_matches}")

        if operator == "AND":
            result = result and pattern_matches
        else:  # OR
            result = result or pattern_matches
        print(f"Combined result with {operator}: {result}")

    print(f"\n✓ Final result: {result} (Expected: True)")
    assert result == True, "Test Case 1 failed!"

    # Test "Barn training"
    test_text = "Barn training"
    result = CategoryService._match_pattern(test_text, patterns_or[0])
    for i in range(1, len(patterns_or)):
        pattern = patterns_or[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: True)")
    assert result == True, "Test Case 1b failed!"

    # Test "Senior training" (should not match)
    test_text = "Senior training"
    result = CategoryService._match_pattern(test_text, patterns_or[0])
    for i in range(1, len(patterns_or)):
        pattern = patterns_or[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: False)")
    assert result == False, "Test Case 1c failed!"

    # Test Case 2: AND logic
    print("\n\nTest Case 2: AND Logic")
    print("-" * 60)
    patterns_and = [
        {"type": "contains", "value": "ungdom", "case_insensitive": True},
        {"type": "contains", "value": "training", "case_insensitive": True, "operator": "AND"}
    ]

    # Test "Ungdom training" (should match)
    test_text = "Ungdom training"
    result = CategoryService._match_pattern(test_text, patterns_and[0])
    print(f"Pattern 1 matches '{test_text}': {result}")

    for i in range(1, len(patterns_and)):
        pattern = patterns_and[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        print(f"Pattern 2 matches '{test_text}': {pattern_matches}")

        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
        print(f"Combined result with {operator}: {result}")

    print(f"\n✓ Final result: {result} (Expected: True)")
    assert result == True, "Test Case 2 failed!"

    # Test "Ungdom match" (should not match - missing "training")
    test_text = "Ungdom match"
    result = CategoryService._match_pattern(test_text, patterns_and[0])
    for i in range(1, len(patterns_and)):
        pattern = patterns_and[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: False)")
    assert result == False, "Test Case 2b failed!"

    # Test "Senior training" (should not match - missing "ungdom")
    test_text = "Senior training"
    result = CategoryService._match_pattern(test_text, patterns_and[0])
    for i in range(1, len(patterns_and)):
        pattern = patterns_and[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: False)")
    assert result == False, "Test Case 2c failed!"

    # Test Case 3: Mixed operators (left-to-right evaluation)
    print("\n\nTest Case 3: Mixed Operators (OR then AND)")
    print("-" * 60)
    patterns_mixed = [
        {"type": "contains", "value": "Fabrikken", "case_insensitive": True},
        {"type": "contains", "value": "Barn", "case_insensitive": True, "operator": "OR"},
        {"type": "contains", "value": "training", "case_insensitive": True, "operator": "AND"}
    ]

    # Test "Fabrikken training" (should match: (true OR false) AND true = true)
    test_text = "Fabrikken training"
    result = CategoryService._match_pattern(test_text, patterns_mixed[0])
    print(f"Pattern 1 matches '{test_text}': {result}")

    for i in range(1, len(patterns_mixed)):
        pattern = patterns_mixed[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        print(f"Pattern {i+1} matches '{test_text}': {pattern_matches}")

        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
        print(f"Combined result with {operator}: {result}")

    print(f"\n✓ Final result: {result} (Expected: True)")
    assert result == True, "Test Case 3 failed!"

    # Test "Barn training" (should match: (false OR true) AND true = true)
    test_text = "Barn training"
    result = CategoryService._match_pattern(test_text, patterns_mixed[0])
    for i in range(1, len(patterns_mixed)):
        pattern = patterns_mixed[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: True)")
    assert result == True, "Test Case 3b failed!"

    # Test "Fabrikken match" (should not match: (true OR false) AND false = false)
    test_text = "Fabrikken match"
    result = CategoryService._match_pattern(test_text, patterns_mixed[0])
    for i in range(1, len(patterns_mixed)):
        pattern = patterns_mixed[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: False)")
    assert result == False, "Test Case 3c failed!"

    # Test "Senior training" (should not match: (false OR false) AND true = false)
    test_text = "Senior training"
    result = CategoryService._match_pattern(test_text, patterns_mixed[0])
    for i in range(1, len(patterns_mixed)):
        pattern = patterns_mixed[i]
        operator = pattern.get("operator", "OR")
        pattern_matches = CategoryService._match_pattern(test_text, pattern)
        if operator == "AND":
            result = result and pattern_matches
        else:
            result = result or pattern_matches
    print(f"✓ '{test_text}' matches: {result} (Expected: False)")
    assert result == False, "Test Case 3d failed!"

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_pattern_matching()
