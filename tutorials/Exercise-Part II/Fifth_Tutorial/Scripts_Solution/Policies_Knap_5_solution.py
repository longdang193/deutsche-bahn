# File containing the implemented Policies

from abc import ABC, abstractmethod
from Environment_Knap_5_solution import KnapsackEnvironment
from Item_Knap_5_solution import Item
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import time
import os

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
           
# Monte carlo reinforcement learning policy class
class MC_RL(Policy):
    
    # constructor
    def __init__(self, 
                n_decision_points: int,
                initial_knap_cap: int,
                initial_lookup_values: int
                ) -> None:
        
        self.n_decision_points = n_decision_points
        self.initial_knap_cap = initial_knap_cap
        self.initial_lookup_values = initial_lookup_values
        self.lookup_table: np.array = np.ones(shape=(self.initial_knap_cap + 1, 
                            self.n_decision_points)) * self.initial_lookup_values # initialize lookup table
        self.n_explored_states: np.array = np.zeros(shape=(self.initial_knap_cap + 1,
                            self.n_decision_points)) # intialize table for counting number of explored states
        return None
    
    # function to make an action based on current state
    def act(self, state: dict) -> bool:
        
        # extract information of state
        item_weight: int = state["Item"].weight # item weight
        item_value: int = state["Item"].value # item value
        remaining_capacity: int = state["Cur_Cap"] # remaining capacity
        cur_decision_point: int = state["Cur_DP"] # current decision point
        
        # check if current item fits into the knapsack
        if remaining_capacity < item_weight:
            return False
        
        cur_decision_point -= 1 # zero index of numpy array
    
        # post-decision state 1: take item
        post_decision_take_cap = remaining_capacity - item_weight
        lookup_tuple = (self.lookup_table.shape[0] - 1 - post_decision_take_cap, 
        cur_decision_point) # inverted index for capacity in lookup tables to have the lookup table created as in the slides
        
        post_decision_take_value = self.lookup_table[lookup_tuple] # get the value of this pds via value function
        
        # post-decision state 2: reject item
        lookup_tuple = (self.lookup_table.shape[0] - 1 - remaining_capacity, cur_decision_point) # inverted index in lookup tables (see above)
        post_decision_reject_value = self.lookup_table[lookup_tuple] # get the value of this pds via value function
        
        # check properties of bellman equation
        if (post_decision_take_value + item_value) >= post_decision_reject_value:
            return True # if pds value + item value (take item) is greater or equal than pds value of not taking item
        else:
            return False # better to reject the item based on pds value

    # method to make stochastic action based on current exploration rate
    def stochastic_action(self, state: dict, exploration_rate: bool) -> bool:
       
        if state["Item"].weight <= state["Cur_Cap"]: # if item fits into knapsack
            if np.random.rand() < exploration_rate: # check current exploration rate
                return np.random.rand() < 0.5 # make stochastic action
            else: # take action based on lookup table
                return self.act(state) # make deterministic action based on current value function
        else: # item does not fit into knapsack
           return False
   
    # method to train a lookup table from scratch
    def train(self,
              knapsack_env: KnapsackEnvironment,
              training_seed: int,
              n_train_epochs: int,
              epsilon_greedy: float,
              display_training_insights: bool,
              path_saved_files: str
              ) -> None:
       
        init_exploration_rate: float = 0.99 # initial exploration rate
        final_exploration_rate: float = 0.01 # final exploration rate
        for epoch in range(n_train_epochs + 1): # loop over training simulation run (epoch)
            exploration_rate: float = init_exploration_rate * (final_exploration_rate / 
                        init_exploration_rate) ** ((epoch / n_train_epochs) ** epsilon_greedy) # compute current exploration rate
            state: dict = knapsack_env.reset(seed=epoch+training_seed) # reset environment
            observed_pds: list = [] # track observed post-decision states
            observed_rewards: list[int] = [] # track observed rewards
            while True: # simulate knapsack problem
                action = self.stochastic_action(state=state, exploration_rate=exploration_rate) # take stochastic action
                state, reward, terminated = knapsack_env.step(action=action) # transition to next state
                observed_pds.append((state["Cur_DP"] - 1, state["Cur_Cap"])) # save observed post-decision state
                observed_rewards.append(reward) # collect observed reward
                if terminated: # simulation has terminated
                    self.update_lookup(observed_pds=observed_pds, 
                            observed_rewards=observed_rewards) # update lookup table, Monte Carlo: update at the end of each epoch
                    if display_training_insights:
                        self.display_training_insights(epoch=epoch, n_train_epochs=n_train_epochs, knapsack_env=knapsack_env, 
                                exploration_rate=exploration_rate, path_saved_files=path_saved_files, init_exploration_rate=init_exploration_rate,
                                final_exploration_rate=final_exploration_rate, epsilon_greedy=epsilon_greedy) # if training information should be displayed and figures are created
                    break # break the current episode
        
        self.lookup_table = np.round(self.lookup_table, decimals=1)
        np.savetxt(path_saved_files + "Lookup_Table_current.txt", self.lookup_table, delimiter=' ', fmt="%.1f") # save lookup table   
        np.savetxt(path_saved_files + "Explored_States_current.txt", self.n_explored_states, delimiter=' ', fmt='%d') # save explored states table
        
        return None        
                            
    # method to update the lookup table
    def update_lookup(self, observed_pds: list, observed_rewards: list) -> None:
        
        observed_rewards.pop(0) # first reward does not belong to a post decision state
        observed_rewards.append(0) # value function of last post decision state has no reward because episode terminates
        # calculate sum of future rewards from each post-decision state on
        future_rewards_pds: list = np.cumsum(np.array(observed_rewards)[::-1])[::-1]
        
        # iterate over pairs of observed pds and corresponding sum of oberved future rewards from that pds on
        for pds, fr_pds in zip(observed_pds, future_rewards_pds): # pds and related future rewards
            cur_decision_point = pds[0] - 1 # zero index in final lookup table
            post_decicion_capacity = pds[1] # get remaining capacity of post decision state
            lookup_tuple = (self.lookup_table.shape[0] - 1 - post_decicion_capacity, cur_decision_point) # inverted index in lookup tables
            self.n_explored_states[lookup_tuple] += 1 # update explored states table
            n_times_observed = self.n_explored_states[lookup_tuple] # check past frequency
            """
            # update alternative 1, outcomment if following update alternative 2 is used
            if n_times_observed == 1: # first time this post decision state is observed
                self.lookup_table[lookup_tuple] = fr_pds # set to observed future reward of pds
            else: # state observed more than once
                # update based on running mean between previous value functions and new observation (future rewards)   
                new_vf_pds = (n_times_observed - 1) / n_times_observed * self.lookup_table[
                    lookup_tuple] + fr_pds / n_times_observed 
                self.lookup_table[lookup_tuple] = new_vf_pds # store new value function in lookup table
            
            """
            # update alternative 2, outcomment if previous update alternative 1 is used
            step_size: float = 1 / (np.sqrt(n_times_observed)) # step size according to frequency of state visit
            old_vf: float = self.lookup_table[lookup_tuple] # get old value function from lookup table
            diff: float = fr_pds - old_vf # calculate difference
            self.lookup_table[lookup_tuple] = old_vf + step_size * diff # update value function in lookup table
              
        return None
    
    # method to evaluate intermediate performance during training
    def evaluation(self, knapsack_env: KnapsackEnvironment, test_instances: int) -> float:
       
        rewards: list[float] = [] # list of rewards
        for test_instance in range(test_instances): # simulation runs
            state = knapsack_env.reset(seed=test_instance+test_instances) # reset environment
            while True: # runing one simulation episode
                action: bool = self.act(state=state) # take action based on current state
                state, _, terminated = knapsack_env.step(action=action) # transition to next state
                if terminated: # simulation run is over
                    rewards.append(knapsack_env.total_reward / knapsack_env.sum_item_value) # track reward
                    break
    
        return np.mean(rewards) # return mean reward
    
    # method to plot training insights
    def display_training_insights(self, epoch: int, n_train_epochs: int, knapsack_env: KnapsackEnvironment, 
                                  exploration_rate: float, path_saved_files: str, init_exploration_rate: float, 
                                  final_exploration_rate: float, epsilon_greedy: float) -> None:
        
        evaluation_step: int = 10 # frequency of each evaluation step within training process (in %)
        if epoch % int(n_train_epochs / (100 / evaluation_step)) == 0: # check intermediate policy performance
            if epoch == 0: # training start
                performance: float = self.evaluation(knapsack_env=knapsack_env, 
                                    test_instances=200) # performance based on initialized lookup table
                explored_states: float = 0.0 # no explored state so far
                print("\nTraining Start Monte Carlo Reinforcement Learning Policy")
                print("Training Progress: {}%\t \u2300 Reward {:.3f}\t Exploration Rate: {:.2f} Explored States: {:.1f}%\t".format(
                    0, performance, exploration_rate, explored_states))
            else: # intermediate training performance
                performance: float = self.evaluation(knapsack_env=knapsack_env, 
                                    test_instances=200) # performance based on current (updated) lookup table
                explored_states: float = np.sum(self.n_explored_states != 0) / (self.lookup_table.shape[0] * 
                                        self.lookup_table.shape[1]) * 100 # percentage of explored states
                print("Training Progress: {}%\t \u2300 Reward {:.3f}\t Exploration Rate: {:.2f} Explored States: {:.1f}%\t ".format(
                    int(100 * epoch/ n_train_epochs), performance, exploration_rate, explored_states))
                if epoch == n_train_epochs: # plotting final lookup table and observed post-decision states
                    self.plot_exploration(path_saved_files=path_saved_files, n_train_epochs=n_train_epochs, # plot exploration over epochs
                        init_exploration_rate=init_exploration_rate, final_exploration_rate=final_exploration_rate, epsilon_greedy=epsilon_greedy) 
                    self.plot_lookup_table(path_saved_files=path_saved_files) # plot final lookup table
                    if int(explored_states) != 100: # no plotting if all post-decision states have been explored
                        self.plot_state_exploration(path_saved_files=path_saved_files) # plot state exploration
        
        return None
    
    # method to plot the exploration over epochs
    def plot_exploration(self, path_saved_files: str, n_train_epochs: int, init_exploration_rate: float, 
                         final_exploration_rate: float, epsilon_greedy: float) -> None:
        
        epochs: np.array = np.arange(n_train_epochs + 1) # create a numpy array for epoch range

        # Calculate exploration rate for each epoch
        exploration_rate: np.array = init_exploration_rate * (final_exploration_rate / init_exploration_rate) ** (
            (epochs / n_train_epochs) ** epsilon_greedy) # calculate exploration rate per epoch

        plt.figure(figsize=(10, 10))
        plt.plot(epochs, exploration_rate, label=f"ε-greedy decay rate = {epsilon_greedy}")
        plt.title("Exploration Rate Decay over Epochs")
        plt.xlabel("Training Epoch")
        plt.ylabel("Magnitude")
        plt.grid(True)
        plt.legend()
        plt.savefig(path_saved_files + "Exploration_Rate_current.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
            
    # method to plot lookup table
    def plot_lookup_table(self, path_saved_files: str) -> None:
        
        surrogate_array = self.lookup_table.copy()
        fig, ax = plt.subplots(figsize=(10, 10))
        heat_map = ax.imshow(surrogate_array, cmap="viridis", interpolation="nearest", aspect="auto")
        plt.colorbar(heat_map, label="PDS Value")
        start_x = int(self.n_decision_points / 5)
        x_labels = [1] + [x for x in range(start_x, self.n_decision_points + 1, start_x)]
        ax.set_xlim(0, self.n_decision_points - 1)
        ax.set_xticks([x - 1 for x in x_labels])
        ax.set_xticklabels(x_labels)
        start_y = int(self.initial_knap_cap / 5)
        y_labels = [0] + [y for y in range(start_y, self.initial_knap_cap + 1, start_y)]
        ax.set_ylim(0, self.initial_knap_cap)
        ax.set_yticks([y for y in reversed(y_labels)])
        ax.set_yticklabels(y_labels)
        ax.invert_yaxis()
        plt.xlabel("Decision Point")
        plt.ylabel("Remaining PDS Capacity")
        plt.title("Final PDS-Values after Training")
        plt.savefig(path_saved_files + "Post-Decision_Values_current.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
        
        return None
    # method to plot visited post-decision states
    def plot_state_exploration(self, path_saved_files: str) -> None:
        
        surrogate_array = np.where(self.n_explored_states == 0, 0, np.where(self.n_explored_states >= 1, 1, 0))
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(surrogate_array, cmap="viridis", interpolation="nearest", aspect="auto")
        cmap = plt.get_cmap("viridis", 2)  
        color_0 = cmap(0)
        color_1 = cmap(1)
        legend_labels = [mpatches.Patch(color=color_1, label="Explored"), 
                         mpatches.Patch(color=color_0, label="Not Explored")]  
        ax.legend(handles=legend_labels, loc="upper right", 
                  facecolor='white', framealpha=1, edgecolor='white', fontsize=15)
    
        start_x = int(self.n_decision_points / 5)
        x_labels = [1] + [x for x in range(start_x, self.n_decision_points + 1, start_x)]
        ax.set_xlim(0, self.n_decision_points - 1)
        ax.set_xticks([x - 1 for x in x_labels])
        ax.set_xticklabels(x_labels)
        start_y = int(self.initial_knap_cap / 5)
        y_labels = [0] + [y for y in range(start_y, self.initial_knap_cap + 1, start_y)]
        ax.set_ylim(0, self.initial_knap_cap)
        ax.set_yticks([y for y in reversed(y_labels)])
        ax.set_yticklabels(y_labels)
        ax.invert_yaxis()
        plt.xlabel("Decision Point")
        plt.ylabel("Remaining PDS Capacity")
        plt.title("Explored States During Training")
        plt.savefig(path_saved_files + "Explored_States_current.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
        
        return None

    # function to load a lookup table if available
    def load_lookup_table(self, path_lookup: str) -> bool:
        
        if os.path.isfile(path_lookup): # check if pretrained lookup table is available
            print("Lookup table for Monte Carlo policy available")    
            self.lookup_table = np.loadtxt(path_lookup) # load lookup table from working directory
            return True
        else:
            return False

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