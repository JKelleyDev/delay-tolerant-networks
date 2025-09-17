"""
Delay-Tolerant Network (DTN) implementation for satellite communication.

This package provides fundamental DTN bundle data structures and operations
for handling messages in satellite communication networks with long delays
and intermittent connectivity.
"""

__version__ = "0.1.0"
__author__ = "Pair 1 - DTN Development Team"

from .bundle import Bundle, BundlePriority

__all__ = ["Bundle", "BundlePriority"]
