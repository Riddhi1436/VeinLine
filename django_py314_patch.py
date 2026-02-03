"""
Monkey-patch for Django 5.1.6 + Python 3.14 Context.__copy__ bug.

The issue occurs because in Python 3.14, the `__dict__` assignment on a `super` object
is no longer allowed. We patch the Context.__copy__ method to fix this.

Error: AttributeError: 'super' object has no attribute 'dicts' and no __dict__ for setting new attributes
"""

import copy
from django.template.context import Context, BaseContext


def patched_context_copy(self):
    """
    Patched __copy__ method that works with Python 3.14.
    
    Creates a shallow copy of the Context without using super().__copy__(),
    which fails in Python 3.14 due to 'super' object __dict__ restrictions.
    """
    # Create a bare instance without calling __init__
    cls = self.__class__
    duplicate = cls.__new__(cls)
    
    # Copy all instance attributes from the original context
    # This is safer than manually listing attributes
    for key, value in self.__dict__.items():
        if key == 'dicts':
            # For dicts, create a shallow copy of the list (but same dict references inside)
            setattr(duplicate, key, value[:])
        else:
            # For other attributes, just assign the reference
            setattr(duplicate, key, value)
    
    return duplicate


# Apply the patch to both Context and any subclass that inherits __copy__
from django.template.context import RequestContext

Context.__copy__ = patched_context_copy
RequestContext.__copy__ = patched_context_copy

__all__ = []


