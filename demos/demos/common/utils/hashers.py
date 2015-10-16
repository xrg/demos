# File: hashers.py

from django.contrib.auth.hashers import PBKDF2PasswordHasher

class CustomPBKDF2PasswordHasher(PBKDF2PasswordHasher):
	"""A subclass of PBKDF2PasswordHasher that uses 1000 iterations."""
	
	iterations = 1000
	algorithm = "custom_pbkdf2"
