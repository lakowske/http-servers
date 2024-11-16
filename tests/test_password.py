"""
This module contains unit tests for the password module.  It checks
the functionality of the password module functions, including testing
the shannon entropy calculation and password strength classification.
"""
import unittest
from http_servers.password import get_char_sets, shannon_entropy, get_entropy, get_password_strength, random_password

class TestPasswordModule(unittest.TestCase):
    """
    TestPasswordModule contains unit tests for password-related functions.

    Methods:
        test_get_char_sets(self):
            Tests the get_char_sets function to ensure it correctly identifies character sets in a given string.

        test_shannon_entropy(self):
            Tests the shannon_entropy function to ensure it correctly calculates the Shannon entropy of a given string.

        test_get_entropy(self):
            Tests the get_entropy function to ensure it correctly calculates the entropy of a given string, considering character sets and common patterns.

        test_get_password_strength(self):
            Tests the get_password_strength function to ensure it correctly categorizes password strength based on entropy values.
    """

    def test_get_char_sets(self):
        """
        Test the get_char_sets function to ensure it correctly identifies character sets.
        Tests:
        - Lowercase characters
        - Uppercase characters
        - Digits
        - Special characters
        - Combination of all character sets
        """
        self.assertEqual(get_char_sets("abc"), {"lowercase"})
        self.assertEqual(get_char_sets("ABC"), {"uppercase"})
        self.assertEqual(get_char_sets("123"), {"digits"})
        self.assertEqual(get_char_sets("!@#"), {"special"})
        self.assertEqual(get_char_sets("aA1!"), {"lowercase", "uppercase", "digits", "special"})

    def test_shannon_entropy(self):
        """
        Test the shannon_entropy function to ensure it correctly calculates the Shannon entropy.
        Tests:
        - Empty string
        - Repeated characters
        - Random characters
        - Increasing complexity
        """
        self.assertAlmostEqual(shannon_entropy("aaa"), 0.0)
        self.assertAlmostEqual(shannon_entropy("abc"), 1.58496, places=5)
        self.assertAlmostEqual(shannon_entropy("aabbcc"), 1.58496, places=5)
        self.assertAlmostEqual(shannon_entropy("abcd"), 2.0)

    def test_get_entropy(self):
        self.assertEqual(get_entropy(""), 0.0)
        self.assertLess(get_entropy("aaa"), 25.0)
        self.assertLess(get_entropy("abc"), 25.0)
        self.assertLess(get_entropy("aabbcc"), 25.0)
        self.assertLess(get_entropy("abcd"), 25.0)
        self.assertLess(get_entropy("aA1!"), 50.0)
        self.assertLess(get_entropy("password"), 25.0)
        self.assertGreater(get_entropy(random_password(20)), 100)  # Penalized for common pattern

    def test_get_password_strength(self):
        self.assertEqual(get_password_strength(0), "Very Weak")
        self.assertEqual(get_password_strength(24), "Very Weak")
        self.assertEqual(get_password_strength(25), "Weak")
        self.assertEqual(get_password_strength(49), "Weak")
        self.assertEqual(get_password_strength(50), "Moderate")
        self.assertEqual(get_password_strength(74), "Moderate")
        self.assertEqual(get_password_strength(75), "Strong")
        self.assertEqual(get_password_strength(99), "Strong")
        self.assertEqual(get_password_strength(100), "Very Strong")

if __name__ == '__main__':
    unittest.main()
