# File containing the implemented Policies

from abc import ABC, abstractmethod

from pandas.io.parsers.base_parser import parsers
from Environment_Knap_3 import KnapsackEnvironment
from Item_Knap_3 import Item
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
    
    """
    Complete the reserve_cap policy class by defining the constructor method and act method
    Hint: Calculate an reduced (artificial) capacity as explained in the lecture (p.26)
    """
    # constructor
    def __init__():

        pass

    def act():
        
        pass
        
          
# Sample based Policy Class
class Sample(Policy):
    
    """
    Complete the sample policy class by defining the constructor method and act method
    Hint: Follow the idea of a sampling-based approach from the lecture (p.32)
    """

    # constructor
    def __init__():

        pass

    def act():
        
        pass
                
# Perfect Information Policy Class  
class Perfect_Information(Policy):

    """
    Complete a perfect information policy assuming that all the items are known in advance
    Hint: Use dynamic programming to solve the static, deterministic version of the knapsack problem
    """
        
    # function to solve static and deterministic knapsack problem to optimality assuming perfect information
    def act():
        
        pass

       
        
        
        
        