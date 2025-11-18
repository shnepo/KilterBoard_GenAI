from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


@dataclass
class Hold:
    id: int
    x: float       # board coordinate
    y: float       # board coordinate
    hold_type: str # crimp, sloper, jug, etc.
    size: float    # optional (0 = tiny, 1 = huge)


@dataclass
class Route:
    holds: List[int]                       # list of hold IDs
    start_holds: List[int] = field(default_factory=list)
    top_hold: Optional[int] = None
    metadata: Dict = field(default_factory=dict)

    # populated after linking holds to dataset
    hold_objects: Dict[int, Hold] = field(default_factory=dict)

    def add_hold(self, hold_id: int):
        self.holds.append(hold_id)

    def remove_hold(self, hold_id: int):
        if hold_id in self.holds:
            self.holds.remove(hold_id)

    def set_start(self, hold_ids: List[int]):
        self.start_holds = hold_ids

    def set_top(self, hold_id: int):
        self.top_hold = hold_id

    
    # COMPUTED PROPERTIES
    def total_move_distance(self) -> float:
        """Sum of distances between consecutive holds."""
        if not self.hold_objects or len(self.holds) < 2:
            return 0.0

        dist = 0.0
        for h1, h2 in zip(self.holds[:-1], self.holds[1:]):
            dist += self._euclidean_distance(self.hold_objects[h1], self.hold_objects[h2])

        return dist

    def avg_move_distance(self) -> float:
        if len(self.holds) < 2:
            return 0.0
        return self.total_move_distance() / (len(self.holds) - 1)

    def avg_hold_size(self) -> float:
        """Average hold size based on dataset."""
        if not self.hold_objects:
            return 0.0

        sizes = [self.hold_objects[h].size for h in self.holds if h in self.hold_objects]
        if not sizes:
            return 0.0
        return sum(sizes) / len(sizes)

    def _euclidean_distance(self, h1: Hold, h2: Hold) -> float:
        return ((h1.x - h2.x)**2 + (h1.y - h2.y)**2) ** 0.5

    # Nice helper for debugging
    def summary(self) -> Dict:
        return {
            "holds": self.holds,
            "start": self.start_holds,
            "top": self.top_hold,
            "avg_move_dist": round(self.avg_move_distance(), 2),
            "avg_hold_size": round(self.avg_hold_size(), 2)
        }

##Testing
