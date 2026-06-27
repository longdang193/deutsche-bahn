# File containing the implemented Policies

from abc import ABC, abstractmethod
from Environment_Knap_3_solution import KnapsackEnvironment
from Item_Knap_3_solution import Item
import numpy as np
import time

# Abstract Policy Class that represents the Super Class for all inheriting Policy Subclasses
class Policy(ABC):
    
    @abstractmethod # "act" method must be implemented by all subclasses
    def act(self, state: dict) -> None:
        pass
        return None         
  
# Greedy Policy Class
class Greedy(Policy):
    
    def act(self, state: dict) -> bool: # returns True if the item can be packed and False if not
        return state["Item"].weight <= state["Cur_Cap"]

# Threshold Policy Class
class Threshold(Policy):

    def __init__(self, threshold: float) -> None:

        self.threshold: float = threshold # threshold value for threshold policy
        return None
    
    def act(self, state: dict) -> bool: # returns True if the item can be packed and False if not

        if state["Item"].weight <= state["Cur_Cap"]:
            return state["Item"].value / state["Item"].weight >= self.threshold

        else:
            return False

# Reserve Cap Policy Class  
class Reserve_Cap(Policy):
    
     # constructor
    def __init__(self, initial_knap_cap: int, n_decision_points: int) -> None:

        self.initial_knap_cap: int = initial_knap_cap # initial knapsack capacity
        self.n_decision_points: int = n_decision_points # number of decision points
        
        return None
        
    # function to make an action based on current state
    def act(self, state: dict) -> bool:

        if state["Cur_Cap"] < state["Item"].weight:
            return False
        else: 
            reduced_cap: float = state["Cur_Cap"] - (
                (self.n_decision_points - state["Cur_DP"]) * self.initial_knap_cap / self.n_decision_points
            )
            return state["Item"].weight <= reduced_cap
          
# Sample based Policy Class
class Sample(Policy):
    
    # constructor
    def __init__(self, sampled_items: int, expected_mean_weight_item: int, 
                 std_deviation_weight_item: float, correlation_factor: float) -> None:
        
        self.sampled_items: int = sampled_items # number of items to sample
        self.expected_mean_weight_item = expected_mean_weight_item # mean item weight
        self.std_deviation_weight_item = std_deviation_weight_item # weight deviation per item
        self.correlation_factor = correlation_factor # define correlation factor
        self.rng = np.random.default_rng() # local RNG independent of global np.random.seed state

        return None
    
    # function to make an action based on current state
    def act(self, state: dict) -> bool:
        
        # check if current item fits into the knapsack
        if state["Cur_Cap"] < state["Item"].weight:
            return False
        
        # draw seeds from local RNG (unaffected by Item() resetting global state)
        seeds: list[int] = [int(self.rng.integers(low=1, high=10000)) for _ in range(self.sampled_items)]
        
        # sample items
        item_list: list[Item] = [] # list of items
        for i in range(self.sampled_items): # loop to create an item for each decision point
            item_list.append(
                    Item(
                    item_id=i, 
                    seed=seeds[i], 
                    expected_mean_weight_item=self.expected_mean_weight_item,
                    std_deviation_weight_item=self.std_deviation_weight_item, 
                    correlation_factor=self.correlation_factor
                    )
            ) # create and append item to item list
        value_share_item: float = state["Item"].value / state["Item"].weight # define value share of current item
        average_value_share: float = sum(item.value / item.weight for item in item_list) / len(item_list)
                                    # get average value/weight share of sample items
        return value_share_item >= average_value_share # take item if it is better than the average of sampled items
           
# Perfect Information Policy Class  
class Perfect_Information(Policy):
        
    # function to solve static and deterministic knapsack problem to optimality assuming perfect information
    def act(self, env: KnapsackEnvironment, n_simulation: int, seed: int) -> (list[float], list[float]):
        
        time_start = time.time() # get current time
        final_reward: list[float] = [] # define list of final rewards
        num_items: int = env.n_decision_points # number of items 
        knapsack_cap: int = env.knapsack_cap_default # default knapsack capacity
        for i in range(n_simulation): # simulation runs
            _ = env.reset(seed=i+seed) # reset knapsack environment
            state_stage: np.array = np.zeros(shape=(num_items + 1, knapsack_cap + 1)) # initialize state-stage table
            weights: list[int] = [item.weight for item in env.item_list] # get list of item weights
            values: list[int] = [item.value for item in env.item_list] # get list of item values
            for n in range(1, num_items + 1): # for all items (stages) 
                for c in range(knapsack_cap + 1): # for all remaining knapsack capacitites (states)
                    if weights[n - 1] <= c: # if item fits
                        # take maximum of either packing or not packing the item
                        state_stage[n][c] = max(state_stage[n - 1][c], values[n - 1] + state_stage[n - 1][c - weights[n - 1]])
                    else:
                        state_stage[n][c] = state_stage[n - 1][c] # proceed with value of previous stage
            final_reward.append(state_stage[num_items][knapsack_cap] / env.sum_item_value) # append relative reward
        
        max_reward: float = round(np.max(final_reward), 3)  # get maximum reward of a single simulation run
        final_reward: float = round(np.mean(final_reward), 3) # get mean reward of all simulation runs
        runtime_test: float = round((time.time() - time_start) / 60, 1) # compute computational runtime
        
        return final_reward, max_reward, runtime_test # return metrics