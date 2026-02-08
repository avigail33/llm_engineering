
# Be careful to support large numbers

def lcg(seed, a=1664525, c=1013904223, m=2**32):
    """
    A Linear Congruential Generator (LCG) that yields a sequence of pseudo-random numbers.
    
    The generator uses the formula: X_{n+1} = (a * X_n + c) % m
    
    Args:
        seed (int): The initial seed value (X_0).
        a (int): The multiplier constant. Default is 1664525 (Numerical Recipes).
        c (int): The increment constant. Default is 1013904223 (Numerical Recipes).
        m (int): The modulus. Default is 2^32.
        
    Yields:
        int: The next pseudo-random number in the sequence.
    """
    value = seed
    while True:
        # Apply the linear congruential formula
        value = (a * value + c) % m
        yield value
        
def max_subarray_sum(n, seed, min_val, max_val):
    """
    Generates a list of random numbers and finds the maximum sum of a contiguous subarray
    using the brute-force O(n^2) approach.
    
    Args:
        n (int): The number of random numbers to generate.
        seed (int): The seed for the LCG to generate the numbers.
        min_val (int): The minimum possible value for the random numbers.
        max_val (int): The maximum possible value for the random numbers.
        
    Returns:
        int: The maximum sum found in the array.
    """
    lcg_gen = lcg(seed)
    # Generate a list of n random integers within the range [min_val, max_val]
    random_numbers = [next(lcg_gen) % (max_val - min_val + 1) + min_val for _ in range(n)]
    
    # Initialize max_sum to negative infinity to handle arrays with all negative numbers
    max_sum = float('-inf')
    
    # Iterate over all possible starting points of the subarray
    for i in range(n):
        current_sum = 0
        # Iterate over all possible ending points of the subarray starting at i
        for j in range(i, n):
            current_sum += random_numbers[j]
            # Update max_sum if the current subarray sum is greater
            if current_sum > max_sum:
                max_sum = current_sum
                
    return max_sum

def total_max_subarray_sum(n, initial_seed, min_val, max_val):
    """
    Runs the max_subarray_sum function 20 times with different seeds derived from
    an initial seed, and sums the results.
    
    Args:
        n (int): The number of random numbers per run.
        initial_seed (int): The base seed used to generate seeds for the 20 runs.
        min_val (int): Minimum value for random numbers.
        max_val (int): Maximum value for random numbers.
        
    Returns:
        int: The total sum of the maximum subarray sums from 20 runs.
    """
    total_sum = 0
    lcg_gen = lcg(initial_seed)
    
    # Perform the calculation 20 times
    for _ in range(20):
        # Generate a new seed for each iteration to ensure different random sequences
        seed = next(lcg_gen)
        total_sum += max_subarray_sum(n, seed, min_val, max_val)
        
    return total_sum

# Parameters
n = 10000         # Number of random numbers in each array
initial_seed = 42 # Initial seed for the LCG
min_val = -10     # Minimum value of random numbers
max_val = 10      # Maximum value of random numbers

# Timing the function
import time
start_time = time.time()
result = total_max_subarray_sum(n, initial_seed, min_val, max_val)
end_time = time.time()

print("Total Maximum Subarray Sum (20 runs):", result)
print("Execution Time: {:.6f} seconds".format(end_time - start_time))
