"""
Unit tests for password generation and validation functions.
Fast tests with no external dependencies.
"""

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
        """Test that passwords contain only letters and numbers with correct proportions"""
        password = random_password(10)

        # Should only contain letters and numbers
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        for char in password:
            assert char in allowed_chars, f"Password contains unexpected character: {char}"

        # Should contain both letters and numbers
        char_sets = get_char_sets(password)
        assert "digits" in char_sets, "Password should contain digits"
        assert "lowercase" in char_sets or "uppercase" in char_sets, "Password should contain letters"

        # Test character proportions for a known length
        digit_count = sum(1 for char in password if char.isdigit())
        letter_count = sum(1 for char in password if char.isalpha())

        # For 10 character password: 2 digits (20%) and 8 letters (80%)
        assert digit_count == 2, f"Expected 2 digits, got {digit_count}"
        assert letter_count == 8, f"Expected 8 letters, got {letter_count}"

    def test_random_password_proportions(self):
        """Test that password proportions are correct for various lengths"""
        test_cases = [
            (5, 1, 4),  # 5 chars: 1 digit (20%), 4 letters (80%)
            (10, 2, 8),  # 10 chars: 2 digits (20%), 8 letters (80%)
            (20, 4, 16),  # 20 chars: 4 digits (20%), 16 letters (80%)
            (25, 5, 20),  # 25 chars: 5 digits (20%), 20 letters (80%)
        ]

        for length, expected_digits, expected_letters in test_cases:
            password = random_password(length)
            digit_count = sum(1 for char in password if char.isdigit())
            letter_count = sum(1 for char in password if char.isalpha())

            assert (
                digit_count == expected_digits
            ), f"Length {length}: expected {expected_digits} digits, got {digit_count}"
            assert (
                letter_count == expected_letters
            ), f"Length {length}: expected {expected_letters} letters, got {letter_count}"
            assert len(password) == length, f"Password length should be {length}, got {len(password)}"

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
