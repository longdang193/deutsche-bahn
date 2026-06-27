# Main file to execute the dynamic knapsack problem

# Import required libraries and class
from Environment_Knap_2_Solution import KnapsackEnvironment
from Policies_Knap_2_Solution import Policy, Greedy
import pandas as pd
import time

# Function to evaluate the performance of any policy
def evaluate_policy(env: KnapsackEnvironment, policy: Policy, n_simulation: int, seed: int):

    total_reward: int = 0 # reset total reward to zero
    max_reward: int = 0 # reset max reward to zero
    runtime_test: float = 0 # reset runtime test to zero
    start_time: float = time.time() # reset start time to current time
    for i in range(n_simulation): # loop over all simulations
        state: dict = env.reset(seed=seed+i) # reset environment and get initial state
        while True: # loop until termination criterion is met
            action: bool = policy.act(state) # take action based on state
            state, terminated = env.step(action) # transition to next state based on action
            if terminated: # if termination criterion is met
                total_reward += env.total_reward # add total reward to total reward
                max_reward = max(max_reward, env.total_reward) # update max reward
                break # break loop
        
    runtime_test: float = round(time.time() - start_time, 2) # calculate runtime test
    average_reward: float = total_reward / n_simulation # calculate average reward
    return average_reward, max_reward, runtime_test # return average reward, max reward, and runtime test

    """
    TODO: Complete the function "evaluate_policy" that evaluates the performance of any given policy
    1. Arguments: knapsack environment, policy, number of simulations, random seed
    2. Create a simulation loop over all simulations where the environment is reset before the start of each simulation episode, 
    actions are taken, and the environment transitions to the next state
    3. Check the termination criterion to break the loop and save collected rewards of current simulation episode
    4. Save the maximum reward across all simulations
    5. Save the average reward across all instances
    6. Calculate the computational runtime
    7. Return the metrics from task 4-6
    """

# Execute only when this script is run as the main programm, does not execute when being an imported module in another file
if __name__ == "__main__":
    
    # Simulation Parameters
    n_decision_points: int = 20 # number of decision points (items) per simulation
    expected_total_weight_items: int = 200 # expected sum of all item weights
    expected_mean_weight_item: int = int(expected_total_weight_items / n_decision_points) # mean of normal distribution from which item weights are sampled
    std_deviation_weight_item: float = expected_mean_weight_item * 0.5 # standard deviation of normal distribution from which item weights are sampled
    knapsack_cap: float = 0.5 # initial available knapsack capacity (share of expected total item weight)
    correlation_factor: float = 0.5 # bias indicating the correlation between weight and value of each item (0: perfectly uncorrelated, 1: perfectly correlated)
    seed: int = 26 # random seed for same data generation
    n_simulation: int = 100 # number of tested simulations
    
    # Create an object "Environment" from environment class
    knapsack_env: KnapsackEnvironment = KnapsackEnvironment(
        n_decision_points=n_decision_points, 
        expected_total_weight_items=expected_total_weight_items,
        expected_mean_weight_item=expected_mean_weight_item, 
        std_deviation_weight_item=std_deviation_weight_item, 
        knapsack_cap=knapsack_cap, 
        correlation_factor=correlation_factor
        )
    
        # Define final Result Table
    results: pd.DataFrame = pd.DataFrame(columns = ["\u2300 Reward", "Max Reward", "Training Time", "Testing Time"]) # columns
    results.index.name = "Policy" # rename the index column
    
    # List of implemented Policies
    policy_set: list[str] = ["Greedy", "Policy_1", "Policy_2"] # here we later put all policies that we investigate throughout the semester
    
    # Select Subset of implemented Policies for Evaluation
    evaluated_policies: list[str] = ["Greedy", "Own_Policy"] # select policies that should be investigated in the current simulation
    
    # Evaluate Greedy Policy
    if "Greedy" in evaluated_policies: # if greedy policy should be evaluated

        greedy: Greedy = Greedy() # initialize object of greedy policy
        final_reward_greedy, max_reward_greedy, runtime_test_greedy = evaluate_policy(
            env=knapsack_env, policy=greedy, n_simulation=n_simulation, seed=seed) # evaluate performance of greedy policy
        results.loc["Greedy"] = [final_reward_greedy, max_reward_greedy, 0.0, runtime_test_greedy] # save results
    
    print(results)