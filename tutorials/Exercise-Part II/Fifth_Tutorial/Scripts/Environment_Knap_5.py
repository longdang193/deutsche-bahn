# File for creating a dynamic environment class

# Import required Class
from Item_Knap_5 import Item

# Define environment class
class KnapsackEnvironment:
    
    # Constructor function to initialize an environment
    def __init__(
            self,
            n_decision_points: int,
            expected_total_weight_items: int, 
            expected_mean_weight_item: int, 
            std_deviation_weight_item: float, 
            knapsack_cap: float, 
            correlation_factor: float
            ) -> None:
                
        # Given Problem Parameters
        self.n_decision_points: int = n_decision_points # initialize number of decision points (items)
        self.expected_mean_weight_item: int = expected_mean_weight_item # mean weight of each item
        self.std_deviation_weight_item: float = std_deviation_weight_item # standard deviation of item weight
        self.knapsack_cap_default: int = int(knapsack_cap * expected_total_weight_items) # initialize knapsack capacity as share of expected total item weight
        self.correlation_factor: float = correlation_factor # define the correlation between the weight and value of an item

        return None
    
    # Function to create the list of items for the simulation
    def create_items(self, seed: int) -> list[Item]:
        
        item_list: list[Item] = [] # list of items
                
        for item in range(1, self.n_decision_points + 1): # loop to create an item for each decision point
            item_list.append(
                    Item(
                    item_id=item, 
                    seed=seed, 
                    expected_mean_weight_item=self.expected_mean_weight_item,
                    std_deviation_weight_item=self.std_deviation_weight_item, 
                    correlation_factor=self.correlation_factor
                    )
            ) # create and append item to item list

        self.sum_item_value: int = sum(item.value for item in item_list) # sum of all item values
            
        return item_list # return item list
    
    # Function to reset the environment
    def reset(self, seed: int = 0) -> dict:
        
        self.cur_decision_point: int = 1 # start each simulation with first decision point
        self.cur_knapsack_cap: float = self.knapsack_cap_default # start with default knapsack capacity
        self.item_list: list[Item] = self.create_items(seed=seed) # call function to create items
        self.total_reward: int = 0 # reset total reward to zero
        
        return self.get_state # call property method to return current state
    
    # Function to return the current state
    @property # property method to allow attribute-like access instead of method call, allowing for dynamic call 
    def get_state(self) -> dict:
        
        state: dict[str] = {
                      "Cur_DP": self.cur_decision_point,
                      "Cur_Cap": self.cur_knapsack_cap,
                      "Item": self.item_list[self.cur_decision_point - 1]
                      } # relevant information to constitute any decision state in the online knapsack problem
        
        return state # return state
    
    # Function to check the termination criterion of the simulation
    @property # property method to allow attribute-like access instead of method call, allowing for dynamic call 
    def terminated(self) -> bool:
       
        if self.cur_decision_point > self.n_decision_points:
            return True
        
        elif self.cur_knapsack_cap == 0:
            return True
        
        else:
            return False
            
    # Function to transition to the next state
    def step(self, action: bool) -> tuple[dict, bool]:

        reward: int = 0
        if action:
            reward = self.get_state["Item"].value
            self.total_reward += self.get_state["Item"].value
            self.cur_knapsack_cap -= self.get_state["Item"].weight
        self.cur_decision_point += 1
        if self.terminated:
            final_state: dict = {"Cur_DP": self.cur_decision_point, "Cur_Cap": self.cur_knapsack_cap} # define a final state
            return final_state, reward, True # return final state, reward, True if simulation has terminated 
        else:
            return self.get_state, reward, False