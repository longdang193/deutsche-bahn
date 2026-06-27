# File containing the implemented Policies

from abc import ABC, abstractmethod

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