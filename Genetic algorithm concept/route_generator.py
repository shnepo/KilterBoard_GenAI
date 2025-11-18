import random
from typing import Dict, List, Tuple
from route_representation import Route, Hold
from parsing import parse_style, parse_difficulty

def load_dummy_holds(cols=10, rows=10):
    """Returns a dictionary of Hold objects arranged in a simple grid."""
    holds = {}
    hold_id = 0
    for r in range(rows):
        for c in range(cols):
            holds[hold_id] = Hold(
                id=hold_id,
                x=c / (cols - 1),
                y=r / (rows - 1),
                hold_type="generic",
                size=random.uniform(0.2, 0.8)
            )
            hold_id += 1
    return holds


class GeneticRouteGenerator:
    def __init__(self, hold_dataset: Dict[int, Hold]):
        self.holds = hold_dataset
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.2
        self.elite_size = 5
        
    def generate_route(self, difficulty: float, style: Dict) -> Route:
        """Generate a route using genetic algorithm."""
        target_moves = self._moves_from_difficulty(difficulty)
        
        # Initialize population
        population = [self._create_random_route(target_moves) for _ in range(self.population_size)]
        
        best_route = None
        best_fitness = float('-inf')
        
        # Evolution loop
        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = [(route, self._fitness(route, style, difficulty)) 
                            for route in population]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Track best
            if fitness_scores[0][1] > best_fitness:
                best_fitness = fitness_scores[0][1]
                best_route = fitness_scores[0][0]
            
            # Selection: keep elite
            new_population = [route for route, _ in fitness_scores[:self.elite_size]]
            
            # Breeding: create offspring
            while len(new_population) < self.population_size:
                parent1 = self._tournament_select(fitness_scores)
                parent2 = self._tournament_select(fitness_scores)
                child = self._crossover(parent1, parent2)
                
                if random.random() < self.mutation_rate:
                    child = self._mutate(child, target_moves)
                
                new_population.append(child)
            
            population = new_population
        
        # Convert best route to Route object
        return self._to_route_object(best_route)
    
    def _create_random_route(self, num_moves: int) -> List[int]:
        """Create a random valid route."""
        # Start from bottom
        bottom_holds = [h.id for h in self.holds.values() if h.y < 0.2]
        start = random.choice(bottom_holds)
        
        route = [start]
        current = start
        
        for _ in range(num_moves):
            # Find holds above and nearby
            candidates = []
            current_hold = self.holds[current]
            
            for h in self.holds.values():
                if h.id in route:
                    continue
                    
                # Must be upward or slightly lateral
                if h.y < current_hold.y - 0.05:
                    continue
                
                dist = ((h.x - current_hold.x)**2 + (h.y - current_hold.y)**2)**0.5
                if 0.05 < dist < 0.3:
                    candidates.append(h.id)
            
            if not candidates:
                break
                
            next_hold = random.choice(candidates)
            route.append(next_hold)
            current = next_hold
        
        return route
    
    def _fitness(self, route: List[int], style: Dict, difficulty: float) -> float:
        """Evaluate route quality."""
        if len(route) < 3:
            return -1000
        
        score = 0.0
        
        # 1. Upward progression
        y_values = [self.holds[h].y for h in route]
        upward_score = sum(y2 - y1 for y1, y2 in zip(y_values[:-1], y_values[1:]))
        score += upward_score * 100
        
        # 2. Consistent move distances
        distances = []
        for h1, h2 in zip(route[:-1], route[1:]):
            hold1, hold2 = self.holds[h1], self.holds[h2]
            dist = ((hold1.x - hold2.x)**2 + (hold1.y - hold2.y)**2)**0.5
            distances.append(dist)
        
        if distances:
            avg_dist = sum(distances) / len(distances)
            target_dist = 0.1 + style["avg_move_distance"] * 0.1
            dist_variance = sum((d - target_dist)**2 for d in distances) / len(distances)
            score -= dist_variance * 500  # Penalize inconsistency
        
        # 3. Style matching - hold sizes
        hold_sizes = [self.holds[h].size for h in route]
        avg_size = sum(hold_sizes) / len(hold_sizes)
        
        if style["crimpy_level"] > 0.7:
            score += (0.5 - avg_size) * 50  # Reward smaller holds
        elif style["hold_size_preference"] > 0.7:
            score += (avg_size - 0.5) * 50  # Reward larger holds
        
        # 4. Route length matching difficulty
        target_length = 4 + difficulty * 6
        length_penalty = abs(len(route) - target_length) * 10
        score -= length_penalty
        
        # 5. No backtracking
        y_decreases = sum(1 for y1, y2 in zip(y_values[:-1], y_values[1:]) if y2 < y1)
        score -= y_decreases * 20
        
        # 6. Dynamic movement bonus
        if style["dynamic_level"] > 0.7:
            long_moves = sum(1 for d in distances if d > 0.15)
            score += long_moves * 10
        
        return score
    
    def _tournament_select(self, fitness_scores: List[Tuple[List[int], float]], 
                          tournament_size: int = 5) -> List[int]:
        """Select parent using tournament selection."""
        tournament = random.sample(fitness_scores, min(tournament_size, len(fitness_scores)))
        return max(tournament, key=lambda x: x[1])[0]
    
    def _crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Create child by combining two parents."""
        if len(parent1) < 2 or len(parent2) < 2:
            return parent1[:]
        
        # Single-point crossover
        point = random.randint(1, min(len(parent1), len(parent2)) - 1)
        
        child = parent1[:point]
        
        # Add holds from parent2 that aren't already in child
        for hold in parent2:
            if hold not in child:
                child.append(hold)
                if len(child) >= max(len(parent1), len(parent2)):
                    break
        
        return child
    
    def _mutate(self, route: List[int], target_moves: int) -> List[int]:
        """Randomly modify route."""
        route = route[:]
        
        mutation_type = random.choice(['replace', 'insert', 'remove', 'swap'])
        
        if mutation_type == 'replace' and len(route) > 2:
            # Replace a random hold
            idx = random.randint(1, len(route) - 1)
            prev_hold = self.holds[route[idx - 1]]
            
            candidates = [h.id for h in self.holds.values() 
                         if h.id not in route and 
                         h.y >= prev_hold.y - 0.05 and
                         ((h.x - prev_hold.x)**2 + (h.y - prev_hold.y)**2)**0.5 < 0.3]
            
            if candidates:
                route[idx] = random.choice(candidates)
        
        elif mutation_type == 'insert' and len(route) < target_moves + 3:
            # Insert a new hold
            idx = random.randint(1, len(route) - 1)
            prev_hold = self.holds[route[idx - 1]]
            next_hold = self.holds[route[idx]]
            
            # Find holds between prev and next
            mid_x = (prev_hold.x + next_hold.x) / 2
            mid_y = (prev_hold.y + next_hold.y) / 2
            
            candidates = [h.id for h in self.holds.values() 
                         if h.id not in route and
                         abs(h.x - mid_x) < 0.15 and abs(h.y - mid_y) < 0.15]
            
            if candidates:
                route.insert(idx, random.choice(candidates))
        
        elif mutation_type == 'remove' and len(route) > 3:
            # Remove a random hold
            idx = random.randint(1, len(route) - 2)
            route.pop(idx)
        
        elif mutation_type == 'swap' and len(route) > 3:
            # Swap two adjacent holds
            idx = random.randint(1, len(route) - 2)
            route[idx], route[idx + 1] = route[idx + 1], route[idx]
        
        return route
    
    def _moves_from_difficulty(self, diff: float) -> int:
        return int(4 + diff * 30)
    
    def _to_route_object(self, hold_sequence: List[int]) -> Route:
        """Convert hold sequence to Route object."""
        start_holds = hold_sequence[:2] if len(hold_sequence) >= 2 else hold_sequence
        top_hold = hold_sequence[-1] if hold_sequence else None
        
        route = Route(
            holds=hold_sequence,
            start_holds=start_holds,
            top_hold=top_hold
        )
        route.hold_objects = self.holds
        return route


# TESTING
if __name__ == "__main__":
    hold_dataset = load_dummy_holds(cols=10, rows=10)
    generator = GeneticRouteGenerator(hold_dataset)
    
    style = parse_style("crimpy and technical")
    difficulty = parse_difficulty("6B")
    
    route = generator.generate_route(difficulty, style)
    print(f"Generated route with {len(route.holds)} holds")
    print(f"Fitness metrics: {route.summary()}")