
"""
Calculator function to add two numbers.

Parameters:
    number1 (float): The first number to be added.
    number2 (float): The second number to be added.

Returns:
    float: The sum of the two input numbers.
"""

def calculator(number1, number2):
    # Check if both number1 and number2 are numeric
    if not isinstance(number1, (int, float)) or not isinstance(number2, (int, float)):
        raise TypeError("Both inputs must be numbers.")
    
    # Return the sum of the two input numbers
    return number1 + number2
