"""
attacks/__init__.py

This file makes the `attacks` directory a Python package.
It allows importing attack classes from the package.

Example:
    from attacks import SynFloodAttack, ICMPFlood
"""

# Import all attack classes for easy access
from .SynFloodAttack import SynFloodAttack
from .ICMPFlood import ICMPFlood
