# Main file to execute the dynamic knapsack problem

# Import required libraries and class
from Environment_Knap_5_solution import KnapsackEnvironment
from Policies_Knap_5_solution import Policy, Greedy, Threshold, Reserve_Cap, Sample, Perfect_Information, MC_RL
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
            state, _, terminated = env.step(action) # transition to next state based on action
            if terminated: # if termination criterion is met
                total_reward += env.total_reward / env.sum_item_value # add total reward to total reward
                max_reward = round(max(max_reward, env.total_reward / env.sum_item_value), 3) # update max reward
                break # break loop
        
    runtime_test: float = round(time.time() - start_time, 2) # calculate runtime test
    average_reward: float = round(total_reward / n_simulation, 3) # calculate average reward
    return average_reward, max_reward, runtime_test # return average reward, max reward, and runtime test

# Execute only when this script is run as the main programm, does not execute when being an imported module in another file
if __name__ == "__main__":
    
    # Simulation Parameters
    n_decision_points: int = 60 # number of decision points (items) per simulation
    expected_total_weight_items: int = 600 # expected sum of all item weights
    expected_mean_weight_item: int = int(expected_total_weight_items / n_decision_points) # mean of normal distribution from which item weights are sampled
    std_deviation_weight_item: float = expected_mean_weight_item * 0.5 # standard deviation of normal distribution from which item weights are sampled
    knapsack_cap: float = 0.3 # initial available knapsack capacity (share of expected total item weight)
    initial_knap_cap: int = int(knapsack_cap * expected_total_weight_items) # initial knapsack capacity saved as integer
    correlation_factor: float = 0.6 # bias indicating the correlation between weight and value of each item (0: perfectly uncorrelated, 1: perfectly correlated)
    seed: int = 34 # random seed for same data generation
    n_simulation: int = 500 # number of tested simulations
    
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
    results: pd.DataFrame = pd.DataFrame(columns = ["Reward", "Max Reward", "Training Time", "Testing Time"]) # columns
    results.index.name = "Policy" # rename the index column
    
    # List of implemented Policies
    policy_set: list[str] = ["Greedy", "Threshold", "Reserve_Cap", "Sample", "MC_RL", "Perfect_Information"] # here we later put all policies that we investigate throughout the semester
    
    # Select Subset of implemented Policies for Evaluation
    evaluated_policies: list[str] = ["Greedy", "Threshold", "Reserve_Cap", "Sample", "MC_RL", "Perfect_Information"] # select policies that should be investigated in the current simulation
    
    # Evaluate Greedy Policy
    if "Greedy" in evaluated_policies: # if greedy policy should be evaluated

        greedy: Greedy = Greedy() # initialize object of greedy policy
        final_reward_greedy, max_reward_greedy, runtime_test_greedy = evaluate_policy(
            env=knapsack_env, policy=greedy, n_simulation=n_simulation, seed=seed) # evaluate performance of greedy policy
        results.loc["Greedy"] = [final_reward_greedy, max_reward_greedy, 0.00, runtime_test_greedy] # save results
    
    # Evaluate Threshold Policy
    if "Threshold" in evaluated_policies: # if threshold policy should be evaluated
        
        threshold_value: float = 1.1 # threshold value for threshold policy
        
        threshold: Threshold = Threshold(threshold=threshold_value) # initialize object of threshold policy
        final_reward_threshold, max_reward_threshold, runtime_test_threshold = evaluate_policy(
            env=knapsack_env, policy=threshold, n_simulation=n_simulation, seed=seed) # evaluate performance of threshold policy
        results.loc["Threshold"] = [final_reward_threshold, max_reward_threshold, 0.00, runtime_test_threshold] # save results

    
    # evaluate reserve cap policy
    if "Reserve_Cap" in evaluated_policies: # if reserve_cap policy should be evaluated
                
        reserve_cap: Reserve_Cap = Reserve_Cap(
            initial_knap_cap=initial_knap_cap,
            n_decision_points=n_decision_points,
            ) # initialize object of reserve_cap policy
        
        final_reward_reserve_cap, max_reward_reserve_cap, runtime_test_reserve_cap = evaluate_policy(
            env=knapsack_env, 
            policy=reserve_cap, 
            n_simulation=n_simulation, 
            seed=seed
            ) # evaluate performance of reserve_cap policy
        
        results.loc["Reserve_Cap"] = [final_reward_reserve_cap, max_reward_reserve_cap, 0.00, runtime_test_reserve_cap] # save results
    
    # evaluate sample policy
    if "Sample" in evaluated_policies: # if sample policy should be evaluated
        
        sampled_items: int = 3
        
        sample: Sample = Sample(
            sampled_items=sampled_items,
            expected_mean_weight_item=expected_mean_weight_item,
            std_deviation_weight_item=std_deviation_weight_item,
            correlation_factor=correlation_factor
            ) # initialize object of sample policy
        
        final_reward_sample, max_reward_sample, runtime_test_sample = evaluate_policy(
            env=knapsack_env, 
            policy=sample, 
            n_simulation=n_simulation, 
            seed=seed
            ) # evaluate performance of sample policy
        
        results.loc["Sample"] = [final_reward_sample, max_reward_sample, 0.00, runtime_test_sample] # save results
    
        # evaluate monte carlo reinforcement learning policy
    if "MC_RL" in evaluated_policies: # if monte carlo reinforcement learning policy should be evaluated
        
        initial_lookup_values: int = 0 # initial lookup table values
        # Attention: only suitable if problem parameters of test instances are the same the lookup table was (pre)trained on
        use_pre_trained_table: bool = False # if pretrained lookup table should be used
       
        mc_rl: MC_RL = MC_RL(
            n_decision_points=n_decision_points,
            initial_knap_cap=initial_knap_cap,
            initial_lookup_values=initial_lookup_values
            ) # initialize object of monte carlo reinforcement learning policy class
        
        if use_pre_trained_table: # if pretrained lookup table should be used
        
            path_lookup: str = "Fifth_Tutorial/Files/Lookup_table_long.txt" # path of stored lookup table
            
            if mc_rl.load_lookup_table(path_lookup=path_lookup): # if lookup table is available
                runtime_train_mc_rl = 0.0 # no training required
                final_reward_mc_rl, max_reward_mc_rl, runtime_test_mc_rl = evaluate_policy(
                    env=knapsack_env, 
                    policy=mc_rl, 
                    n_simulation=n_simulation, 
                    seed=seed
                    ) # evaluate performance of monte carlo reinforcement learning policy using pretrained lookup table
            
            else: # if lookup table should be used but is not available
                raise FileNotFoundError("No lookup table for Monte Carlo policy available")
        
        else: # if lookup table should be trained from scratch
        
            path_saved_files: str = "Fifth_Tutorial/Files/" # path for saved training_insights    
            display_training_insights: bool = True # if training progress should be displayed and training plots are created
            
            n_train_epochs: int = int(1e2) # number of training epochs
            training_seed: int = 5 # training seed
            epsilon_greedy: float = 2.0 # control of exploration rate, high value -> high exploration
            start_training: float = time.time() # track time of training start
            
            mc_rl.train(knapsack_env=knapsack_env,
                        training_seed=training_seed,
                        n_train_epochs=n_train_epochs,
                        epsilon_greedy=epsilon_greedy,
                        display_training_insights=display_training_insights,
                        path_saved_files=path_saved_files
                        ) # train the policy
            
            runtime_train_mc_rl: float = round((time.time() - start_training) / 60, 1) # compute training time
           
            final_reward_mc_rl, max_reward_mc_rl, runtime_test_mc_rl = evaluate_policy(
                env=knapsack_env, 
                policy=mc_rl, 
                n_simulation=n_simulation, 
                seed=seed
                ) # evaluate performance of monte carlo reinforcement learning policy after training
        
        results.loc["MC_RL"] = [final_reward_mc_rl, max_reward_mc_rl, runtime_train_mc_rl, runtime_test_mc_rl] # save results

        
    # evaluate (optimal) dyncamic programming policy for solving the static, deterministic version of the knapsack problem assuming perfect information
    if "Perfect_Information" in evaluated_policies: # if policy should be evaluated
        
        pi: Perfect_Information = Perfect_Information() # initialize object of perfect information policy
        
        final_reward_perfect_info, max_reward_perfect_info, runtime_test_perfect_information = pi.act(
            env=knapsack_env,
            n_simulation=n_simulation, 
            seed=seed
            ) # evaluate dynamic programming algorithm to solve static knapsack problem
        
        results.loc["PI"] = [final_reward_perfect_info, max_reward_perfect_info, 
        0.00, runtime_test_perfect_information] # save results
    
    print(results)