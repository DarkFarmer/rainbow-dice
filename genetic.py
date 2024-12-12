import random
import numpy as np

# Step 1: Define the genes (strategy weights)
class Strategy:
    def __init__(self, control_point_weight, charge_weight, melee_weight, missile_weight):
        self.control_point_weight = control_point_weight
        self.charge_weight = charge_weight
        self.melee_weight = melee_weight
        self.missile_weight = missile_weight

    def mutate(self):
        """Introduce small random variations."""
        mutation_rate = 0.1
        self.control_point_weight += random.uniform(-mutation_rate, mutation_rate)
        self.charge_weight += random.uniform(-mutation_rate, mutation_rate)
        self.melee_weight += random.uniform(-mutation_rate, mutation_rate)
        self.missile_weight += random.uniform(-mutation_rate, mutation_rate)

    def normalize(self):
        """Ensure weights sum to 1."""
        total = (
            self.control_point_weight
            + self.charge_weight
            + self.melee_weight
            + self.missile_weight
        )
        self.control_point_weight /= total
        self.charge_weight /= total
        self.melee_weight /= total
        self.missile_weight /= total

def evaluate_strategy(strategy, population, baseline_strategy):
    """Evaluate the strategy by playing games against a baseline and peers."""
    wins = 0
    
    # Play against the baseline
    if simulate_game(strategy, baseline_strategy) == "this_strategy":
        wins += 1

    # Play against a few random peers
    for _ in range(3):  # Test against 3 random peers
        opponent_strategy = random.choice(population)
        if simulate_game(strategy, opponent_strategy) == "this_strategy":
            wins += 1

    return wins

# Step 2: Generate the initial population
def generate_population(size):
    population = []
    for _ in range(size):
        strategy = Strategy(
            control_point_weight=random.random(),
            charge_weight=random.random(),
            melee_weight=random.random(),
            missile_weight=random.random(),
        )
        strategy.normalize()
        population.append(strategy)
    return population
# Step 4: Selection
def select_parents(population, fitness_scores):
    """Select top-performing strategies."""
    # Sort by fitness scores (descending order)
    sorted_population = [strategy for _, strategy in sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)]
    return sorted_population[: len(population) // 2]

# Step 5: Crossover
def crossover(parent1, parent2):
    """Combine genes from two parents."""
    child = Strategy(
        control_point_weight=(parent1.control_point_weight + parent2.control_point_weight) / 2,
        charge_weight=(parent1.charge_weight + parent2.charge_weight) / 2,
        melee_weight=(parent1.melee_weight + parent2.melee_weight) / 2,
        missile_weight=(parent1.missile_weight + parent2.missile_weight) / 2,
    )
    child.mutate()
    child.normalize()
    return child

# Step 6: Genetic algorithm loop
def genetic_algorithm(generations, population_size):
    population = generate_population(population_size)
    baseline_strategy = Strategy(
        control_point_weight=1.0,
        charge_weight=1.0,
        melee_weight=1.0,
        missile_weight=1.0,
    )
    for generation in range(generations):
        print(f"Generation {generation + 1}")
        fitness_scores = [
            evaluate_strategy(strategy, population, baseline_strategy)
            for strategy in population
        ]

        # Select parents
        parents = select_parents(population, fitness_scores)

        # Generate next generation
        next_generation = []
        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(parents, 2)
            child = crossover(parent1, parent2)
            next_generation.append(child)

        population = next_generation

        # Print the best strategy of the generation
        best_strategy = parents[0]  # After sorting, the best strategy is the first parent
        print(f"Best strategy: {vars(best_strategy)}")

    return population

# Example: Simulate a game (simplified placeholder)
def simulate_game(strategy, opponent_strategy):
    """Simulate a game using the given strategy against an opponent strategy."""
    # Compare actions like moving, charging, and attacking, based on strategy preferences.
    # Strategy with the highest weighted effectiveness "wins" the game.
    
    strategy_score = (
        strategy.control_point_weight * random.uniform(0.8, 1.2) +
        strategy.charge_weight * random.uniform(0.8, 1.2) +
        strategy.melee_weight * random.uniform(0.8, 1.2) +
        strategy.missile_weight * random.uniform(0.8, 1.2)
    )
    opponent_score = (
        opponent_strategy.control_point_weight * random.uniform(0.8, 1.2) +
        opponent_strategy.charge_weight * random.uniform(0.8, 1.2) +
        opponent_strategy.melee_weight * random.uniform(0.8, 1.2) +
        opponent_strategy.missile_weight * random.uniform(0.8, 1.2)
    )
    
    return "this_strategy" if strategy_score > opponent_score else "opponent"
# Run the genetic algorithm
if __name__ == "__main__":
    final_population = genetic_algorithm(generations=20, population_size=50)
