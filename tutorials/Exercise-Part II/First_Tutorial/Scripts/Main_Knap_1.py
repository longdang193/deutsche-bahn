# Main file to execute the dynamic knapsack problem

# Import required libraries and class
from Environment_Knap_1 import KnapsackEnvironment
from Item_Knap_1 import Item
import pandas as pd

# Execute only when this script is run as the main programm, does not execute when being an imported module in another file
if __name__ == "__main__":
    
    # Simulation Parameters
    n_decision_points: int = 20 # number of decision points (items) per simulation
    expected_total_weight_items: int = 200 # expected sum of all item weights
    expected_mean_weight_item: int = int(expected_total_weight_items / n_decision_points) # mean of normal distribution from which item weights are sampled
    std_deviation_weight_item: float = expected_mean_weight_item * 0.5 # standard deviation of normal distribution from which item weights are sampled
    knapsack_cap: float = 0.5 # initial available knapsack capacity (share of expected total item weight)
    correlation_factor: float = 0.75 # bias indicating the correlation between weight and value of each item (0: perfectly uncorrelated, 1: perfectly correlated)
    seed: int = 26 # random seed for same data generation
        
    # Create an object "Environment" from environment class
    knapsack_env: KnapsackEnvironment = KnapsackEnvironment(
        n_decision_points=n_decision_points, 
        expected_total_weight_items=expected_total_weight_items,
        expected_mean_weight_item=expected_mean_weight_item, 
        std_deviation_weight_item=std_deviation_weight_item, 
        knapsack_cap=knapsack_cap, 
        correlation_factor=correlation_factor
        )
    
    # Show item list
    final_items: pd.DataFrame = pd.DataFrame(columns = ["ID", "Weight", "Value"]) # data frame to store final items
    first_state: dict[str] = knapsack_env.reset(seed=seed) # reset the environment: creates an item list and return first state
    item_list: list[Item] = knapsack_env.item_list # get the item list
    for idx, item in enumerate(item_list): # iterate through item list 
        final_items.loc[idx] = [item.item_id, item.weight, item.value] # unpack item data
        
    """
    TODO: Consider the following tasks regarding the final item list
    1. Save the final item list in a ".txt" file, consider the keyword arguments "sep" to display a clear table
    2. Print out the final item list
    3. Print out the first state
    """