import string
import hashlib
import secrets


def get_gravatar_hash(emailAddress=None):
    """
    Returns the Gravatar hash based on the provided email address.

    :param emailAddress: The email address used to generate the Gravatar hash.
        If not provided, the function returns the hash for an empty string.
    :type emailAddress: str, optional

    :return: The Gravatar hash for the provided email address.
    :rtype: str
    """
    return hashlib.md5(emailAddress.lower().encode("utf-8")).hexdigest()


def generate_secure_password(length=16):
    """Generate a cryptographically secure random password"""
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars),
    ]

    # Fill the rest of the password
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle the password
    secrets.SystemRandom().shuffle(password)

    return "".join(password)
