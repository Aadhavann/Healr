"""
Example file with intentional code quality issues for demonstration.
This file will be analyzed and fixed by Healr.
"""

# Issue: Missing module docstring
# Issue: Unused imports
import os
import sys
import json
import random


# Issue: Missing function docstring
# Issue: Poor naming (single letter variables)
def calc(x, y):
    # Issue: No input validation
    r = x + y
    return r


# Issue: High cyclomatic complexity
def process_data(a, b, c, d, e):
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        result = a + b + c + d + e
                    else:
                        result = a + b + c + d
                else:
                    result = a + b + c
            else:
                result = a + b
        else:
            result = a
    return result


# Issue: Missing docstring, poor error handling
class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        # Issue: Bare except clause
        try:
            return self.data * 2
        except:
            return None

    # Issue: Inconsistent naming convention
    def ProcessMore(self, x):
        return x + 10


# Issue: Unused variable
def calculate_total(items):
    total = 0
    count = 0
    for item in items:
        total += item
        count += 1
    # count is calculated but never used
    return total


# Issue: Dangerous default argument
def add_to_list(item, my_list=[]):
    my_list.append(item)
    return my_list


# Issue: Multiple statements on one line
def quick_calc(x, y): return x + y


# Issue: No error handling, poor naming
def read_file(f):
    data = open(f).read()
    return data


# Issue: Magic numbers
def calculate_discount(price):
    if price > 100:
        return price * 0.9
    elif price > 50:
        return price * 0.95
    else:
        return price


# Issue: Unused function
def unused_helper():
    pass


if __name__ == "__main__":
    # Issue: No error handling
    result = calc(5, 10)
    print(f"Result: {result}")

    # Issue: Variable name shadows built-in
    list = [1, 2, 3, 4, 5]
    print(calculate_total(list))
