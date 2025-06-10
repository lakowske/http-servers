"""
Unit tests for password generation and validation functions.
Fast tests with no external dependencies.
"""

import re

import pytest

from auth.password import get_char_sets, get_entropy, get_password_strength, random_password, shannon_entropy


@pytest.mark.unit
class TestPasswordGeneration:
    """Test password generation functions"""

    def test_random_password_length(self):
        """Test password generation with different lengths"""
        for length in [8, 12, 16, 20, 32]:
            password = random_password(length)
            assert len(password) == length

    def test_random_password_uniqueness(self):
        """Test that generated passwords are unique"""
        passwords = [random_password(16) for _ in range(10)]
        assert len(set(passwords)) == 10, "Generated passwords should be unique"

    def test_random_password_character_sets(self):
        """Test that passwords contain expected character sets"""
        password = random_password(20)

        # Should contain letters and numbers at minimum
        assert re.search(r"[a-zA-Z]", password), "Password should contain letters"
        assert re.search(r"[0-9]", password), "Password should contain numbers"

    def test_get_char_sets(self):
        """Test character set detection"""
        test_cases = [
            ("abc", ["lowercase"]),
            ("ABC", ["uppercase"]),
            ("123", ["digits"]),
            ("!@#", ["special"]),
            ("Abc123!", ["lowercase", "uppercase", "digits", "special"]),
            ("", []),
        ]

        for password, expected_sets in test_cases:
            result = get_char_sets(password)
            assert set(result) == set(expected_sets)

    def test_shannon_entropy(self):
        """Test Shannon entropy calculation"""
        test_cases = [
            ("", 0.0),  # Empty string
            ("aaaa", 0.0),  # All same character
            ("ab", 1.0),  # Two different characters
            ("abcd", 2.0),  # Four different characters
        ]

        for text, expected_entropy in test_cases:
            result = shannon_entropy(text)
            assert abs(result - expected_entropy) < 0.01, f"Entropy for '{text}' should be ~{expected_entropy}"

    def test_get_entropy(self):
        """Test entropy calculation for passwords"""
        # Longer passwords should have higher entropy
        short_password = "abc"
        long_password = "abcdefghijklmnop"

        short_entropy = get_entropy(short_password)
        long_entropy = get_entropy(long_password)

        assert isinstance(short_entropy, (int, float))
        assert isinstance(long_entropy, (int, float))
        assert long_entropy > short_entropy

    def test_get_password_strength(self):
        """Test password strength categorization"""
        # Test with actual entropy values
        test_cases = [
            (0, "Very Weak"),
            (20, "Very Weak"),
            (30, "Weak"),
            (60, "Moderate"),
            (80, "Strong"),
            (120, "Very Strong"),
        ]

        for entropy, expected_strength in test_cases:
            result = get_password_strength(entropy)
            assert result == expected_strength, f"Entropy {entropy} should be {expected_strength}"


@pytest.mark.unit
class TestPasswordEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_length_password(self):
        """Test edge case of zero length password"""
        # Check actual behavior - may return empty string instead of raising
        result = random_password(0)
        assert len(result) == 0

    def test_negative_length_password(self):
        """Test edge case of negative length"""
        # Check actual behavior - may return empty string instead of raising
        result = random_password(-1)
        assert len(result) == 0

    def test_very_long_password(self):
        """Test very long password generation works"""
        password = random_password(1000)
        assert len(password) == 1000
        assert isinstance(password, str)

    def test_unicode_handling(self):
        """Test functions handle unicode characters gracefully"""
        unicode_password = "café123🔒"

        # Functions should not crash with unicode
        char_sets = get_char_sets(unicode_password)
        entropy = get_entropy(unicode_password)
        strength = get_password_strength(entropy)  # Pass entropy, not password

        assert isinstance(char_sets, (list, set))
        assert isinstance(entropy, (int, float))
        assert isinstance(strength, str)
