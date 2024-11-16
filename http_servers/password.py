"""
This module provides functions to evaluate the strength and entropy of passwords.

Functions:
- get_char_sets(password: str) -> Set[str]: Returns the character sets used in the password.
- shannon_entropy(password: str) -> float: Calculates the Shannon entropy of the password string.
- get_entropy(password: str) -> float: Calculates the password entropy considering length, 
  character set complexity, Shannon entropy, and common patterns.
- get_password_strength(entropy: float) -> str: Returns the password strength classification 
  based on entropy.
"""
import re
import math
import random
from collections import Counter
from typing import Set

def random_password(length: int=8) -> str:
    """
    Generates a random password string.

    Args:
        length (int): The length of the password.

    Returns:
        str: The random password.
    """
    random.seed()
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    special = "!@#$%^&*()_+-=[]|;:,.<>?"    
    chars = lowercase + uppercase + numbers + special
    return "".join(random.choices(chars, k=length))

def get_char_sets(password: str) -> Set[str]:
    """Returns the character sets used in password"""
    char_sets = set()
    if re.search(r'[a-z]', password):
        char_sets.add('lowercase')
    if re.search(r'[A-Z]', password):
        char_sets.add('uppercase')
    if re.search(r'[0-9]', password):
        char_sets.add('digits')
    if re.search(r'[^a-zA-Z0-9]', password):
        char_sets.add('special')
    return char_sets

def shannon_entropy(password: str) -> float:
    """
    Calculate Shannon entropy of password string.
    Higher values mean more random/complex passwords.
    """
    # Count character frequencies
    counts = Counter(password)
    
    # Calculate probability of each character
    probabilities = [count/len(password) for count in counts.values()]
    
    # Shannon entropy formula: -sum(p * log2(p))
    return -sum(p * math.log2(p) for p in probabilities)

def get_entropy(password: str, min_repeats: int = 3) -> float:
    """
    Calculates password entropy considering:
    - Length
    - Character set complexity 
    - Shannon entropy
    - Common patterns

    Returns:
        float: Entropy score (higher is better)
    """
    if len(password) == 0:
        return 0.0

    # Base entropy from length and character sets
    char_sets = get_char_sets(password)
    base_entropy = len(password) * len(char_sets) * 2

    # Add Shannon entropy contribution
    shannon = shannon_entropy(password)

    # Penalize common patterns
    penalties = 0
    if get_repeat_count(password) > 0:  # Repeated characters
        penalties += 5
    if re.search(r'(abc|123|qwe|pwd|password)', password, re.I):  # Common sequences
        penalties += 10

    return max(0, base_entropy + shannon - penalties)

def get_repeat_count(password: str) -> int:
    """
    Returns the count of sequentially repeated characters in the password.
    """
    return max(len(re.findall(r'(.)\1{2,}', password)), 0)
    

def get_password_strength(entropy: float) -> str:
    """Returns password strength classification"""
    if entropy < 25:
        return "Very Weak"
    if entropy < 50:
        return "Weak"
    if entropy < 75:
        return "Moderate"
    if entropy < 100:
        return "Strong"
    return "Very Strong"
