# File to define an item class

# Import required Library
import numpy as np

# Define item class
class Item:
    
    # Constructor function to initialize an item
    def __init__(self, 
                 item_id: int, 
                 seed: int, 
                 expected_mean_weight_item: int, 
                 std_deviation_weight_item: float, 
                 correlation_factor: float
                 ) -> None:
        
        self.item_id: int = item_id # assign item ID based on the given argument "item_id"

        np.random.seed(
            seed=seed+self.item_id
            ) # set a random numpy seed to ensure individual item weights and values as well as same data generation across different policies

        self.weight: float = np.random.normal(
            loc=expected_mean_weight_item, 
            scale=std_deviation_weight_item
            ) # sample item weight from normal distribution with the predefined statistics from the arguments

        self.weight: int = max(
            1, int(round((self.weight)))
            ) # if item weight is smaller than 1 (due to distributional properties), set it to 1, else round weights to the closest integer

        self.value: float = correlation_factor * self.weight + (1 - correlation_factor) * np.random.uniform(
            low=expected_mean_weight_item - 2 * std_deviation_weight_item, 
            high=expected_mean_weight_item + 2 * std_deviation_weight_item
            ) # sample item value according to a convex sum based on real item weight and a uniform distribution (covers 95% of realizations of item weights)
        self.value: int = max(1, int(round(self.value)))
            
        return None
    
    # Define representation method for item class
    def __repr__(self) -> str:
        
        return f" Item ID: {self.item_id}, Weight: {self.weight}, Value: {self.value}" # returns relevant information of an item as printed text