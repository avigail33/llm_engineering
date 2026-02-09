
import unittest
from your_module import lcg, max_subarray_sum, total_max_subarray_sum

class TestLCG(unittest.TestCase):

    def test_lcg(self):
        seed = 12345
        a = 1664525
        c = 1013904223
        m = 2**32
        
        lcg_gen = lcg(seed, a, c, m)
        
        self.assertEqual(next(lcg_gen), seed)
        values = list(lcg_gen)
        self.assertEqual(len(values), 1000)  # Assuming max iteration in lcg is 1000 for testing
        for i in range(1, len(values)):
            if abs(values[i] - (a * values[i-1] + c) % m) > 1:
                raise AssertionError("Generated value does not match LCG formula")

    def test_max_subarray_sum(self):
        n = 10
        seed = 12345
        min_val = 0
        max_val = 100
        
        random_numbers = [next(lcg(seed)) % (max_val - min_val + 1) + min_val for _ in range(n)]
        
        max_sum = float('-inf')
        # Testing subarray sum using brute force might not be efficient, consider iterating within bounds instead
        for i in range(n):
            for j in range(i, n):
                current_sum = sum(random_numbers[i:j+1])
                if current_sum > max_sum:
                    max_sum = current_sum
        
        self.assertEqual(max_subarray_sum(n, seed, min_val, max_val), max_sum)
        
    def test_total_max_subarray_sum(self):
        n = 10000
        initial_seed = 12345
        min_val = -10
        max_val = 1
        
        total_sum = total_max_subarray_sum(n, initial_seed, min_val, max_val)
        self.assertGreater(total_sum, 0)   # Assuming max subarray sum should be non-negative
    
class TestLCGMutation(unittest.TestCase):

    def test_lcm_movement_rounds(self):
        seed = 12345
        steps = 20
        initial_seed = next(lcg(seed)) % (2**32)
        
        self.assertEqual(initial_seed, seed)
        
def main():
    import time
    start_time = time.time()
    result = total_max_subarray_sum(1000001 ,42 , -10., 10.)
    end_time = time.time()
    
    print("Total Maximum Subarray Sum (20 runs)::", result)
    print("Execution Time: {:.6f} seconds".format(end_time - start_time))

if __name__ == '__main__':
    unittest.main(exit=False)
    main()

