import random
from typing import Dict, List
from route_representation import Route, Hold
from parsing import parse_style, parse_difficulty
from route_representation import Hold

def load_dummy_holds(cols=10, rows=10):
    """
    Returns a dictionary of Hold objects arranged in a simple grid.
    Coordinates are normalized 0.0 → 1.0.
    Good for quick visualization and prototyping.
    """
    holds = {}
    hold_id = 0

    for r in range(rows):
        for c in range(cols):
            x = c / (cols - 1)      # 0.0 → 1.0 horizontally
            y = r / (rows - 1)      # 0.0 → 1.0 vertically

            holds[hold_id] = Hold(
                id=hold_id,
                x=x,
                y=y,
                hold_type="generic",
                size=0.5
            )
            hold_id += 1

    return holds


class RouteGenerator:
    def __init__(self, hold_dataset: Dict[int, Hold]):
        self.holds = hold_dataset
        
    # CREATE A NEW RANDOM ROUTE
    def generate_route(self, difficulty: float, style: Dict) -> Route:
        """
        difficulty: float 
        style: dict from style_parser
        """

        num_moves = self._moves_from_difficulty(difficulty)

        # Pick 2 random start holds near the bottom
        start = self._sample_start_holds()

        # Generate the rest of the moves
        hold_sequence = start[:]

        current_hold = random.choice(start)

        for _ in range(num_moves):
            next_hold = self._sample_next_hold(current_hold, style, hold_sequence)
            if next_hold is None:
                break
            hold_sequence.append(next_hold.id)
            current_hold = next_hold.id

        # Pick a reasonable top hold (highest y)
        top = self._choose_top_hold(hold_sequence)

        route = Route(
            holds=hold_sequence,
            start_holds=start,
            top_hold=top
        )

        route.hold_objects = self.holds
        return route

    
    # INTERNAL HELPERS
    def _moves_from_difficulty(self, diff: float) -> int:
        """
        More difficult routes should have more moves OR  
        harder moves (modulated by style later).
        """
        return int(4 + diff * 20)  # 4 to 10 moves

    def _sample_start_holds(self) -> List[int]:
        """Choose 2 holds from the bottom 15% of the board."""
        bottom = [h for h in self.holds.values() if h.y < 0.15]
        start = random.sample(bottom, 2)
        return [start[0].id, start[1].id]

    def _sample_next_hold(self, current: int, style: Dict, existing_sequence: List[int]):
        """Pick a hold in the style-preferred distance range with upward bias."""

        current_hold = self.holds[current]

        # Movement distance preferences (smaller target distances)
        base_dist = 0.08 + style["avg_move_distance"] * 0.15  # Range: 0.08 to 0.23
        
        candidates = []
        for hold in self.holds.values():
            # Skip holds already in the route
            if hold.id in existing_sequence:
                continue

            # Bias hold size selection
            if style["crimpy_level"] > 0.7 and hold.size > 0.6:
                continue  # avoid big holds on crimpy problems
            if style["hold_size_preference"] > 0.7 and hold.size < 0.3:
                continue  # avoid small holds on juggy climbs

            # Calculate distance
            dist = ((hold.x - current_hold.x)**2 + (hold.y - current_hold.y)**2)**0.5
            
            # Upward progression: prioritize holds that are higher (lower y is higher on inverted board)
            y_diff = hold.y - current_hold.y
            
            # Must be moving upward or slightly lateral (allow small downward for traverses)
            if y_diff < -0.05:  # moving down too much
                continue
            
            # Distance filtering - tighter range
            min_dist = base_dist * 0.5
            max_dist = base_dist * 1.8
            
            if min_dist < dist < max_dist:
                # Score based on distance to target and upward movement
                dist_score = abs(dist - base_dist)
                upward_bonus = max(0, y_diff) * 2.0  # reward upward movement
                
                # Prefer moves that are upward and at good distance
                score = dist_score - upward_bonus
                candidates.append((score, dist, hold))

        if not candidates:
            # Fallback: just find any hold that's upward and reasonably close
            for hold in self.holds.values():
                if hold.id in existing_sequence:
                    continue
                y_diff = hold.y - current_hold.y
                dist = ((hold.x - current_hold.x)**2 + (hold.y - current_hold.y)**2)**0.5
                if y_diff >= 0 and dist < 0.3:
                    candidates.append((dist, dist, hold))
        
        if not candidates:
            return None

        # Sort by score (lower is better)
        candidates.sort(key=lambda x: x[0])
        
        # Pick from top candidates with some randomness
        top_n = min(5, len(candidates))
        selected = random.choice(candidates[:top_n])
        return selected[2]

    def _choose_top_hold(self, sequence: List[int]) -> int:
        """Pick the hold in the sequence with the highest Y coordinate."""
        return max(sequence, key=lambda h: self.holds[h].y)

## TESTING
# Dummy hold dataset (you will replace with real Kilter holds)
dataset = {
    i: Hold(id=i, x=i%5, y=i//5/10, hold_type="crimp", size=0.5)
    for i in range(1, 50)
}

hold_dataset = load_dummy_holds()
generator = RouteGenerator(hold_dataset)

style = parse_style("crimpy and technical")
difficulty = parse_difficulty("6B")

route = generator.generate_route(difficulty, style)