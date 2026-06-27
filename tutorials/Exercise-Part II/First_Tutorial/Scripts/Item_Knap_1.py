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
        
        """
        TODO: Consider the following tasks regarding the creation of an item
        1. Assign an item ID based on the given argument "item_id", name the variable "item_id"
        2. Set a random numpy seed, set the sum of the item ID and argument "seed" as the numpy seed
        3. Assign an item weight based on a normal distribution with the predefined statistics from the keywords using the numpy library
        4. If an item weight is smaller or equal to 1, set it to 1, else round weights to the closest integer
        5. Assign an item value based on a convex sum between real item weight and a uniform distribution (correlation factor is the balancing factor)
        -> Uniform distribution: the bounds are the lower and upper 2-sigma limits of the normal distribution for weights
        6. If an item value is smaller or equal to 1, set it to 1, else round values to the closest integer
        """
    
        return None
    
    # Define representation method for item class
    def __repr__(self) -> str:
        
        return f" Item ID: {self.item_id}, Weight: {self.weight}, Value: {self.value}" # returns relevant information of an item as printed text