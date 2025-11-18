import sys
sys.path.append('/mnt/data')

import matplotlib.pyplot as plt
from route_generator import GeneticRouteGenerator, load_dummy_holds  # Changed import
from parsing import parse_style, parse_difficulty

# Generate route
hold_dataset = load_dummy_holds(cols=10, rows=10)
gen = GeneticRouteGenerator(hold_dataset)  # Changed class name
style = parse_style("crimpy and technical") 
difficulty = parse_difficulty("8C")  
route = gen.generate_route(difficulty, style)

# All holds
all_x = [h.x for h in hold_dataset.values()]
all_y = [h.y for h in hold_dataset.values()]

# Route holds - separated by type
start_x = [hold_dataset[h].x for h in route.start_holds]
start_y = [hold_dataset[h].y for h in route.start_holds]

end_x = [hold_dataset[route.top_hold].x]
end_y = [hold_dataset[route.top_hold].y]

intermediate_holds = [h for h in route.holds if h not in route.start_holds and h != route.top_hold]
inter_x = [hold_dataset[h].x for h in intermediate_holds]
inter_y = [hold_dataset[h].y for h in intermediate_holds]

# All route holds for the path line
route_x = [hold_dataset[h].x for h in route.holds]
route_y = [hold_dataset[h].y for h in route.holds]

plt.figure(figsize=(6,6))

# Base board (all holds)
plt.scatter(all_x, all_y, s=20, c='lightgray', alpha=0.5, label='All holds')

# Start holds (green)
plt.scatter(start_x, start_y, s=200, c='green', marker='o', label='Start', zorder=5)

# Intermediate holds (blue)
plt.scatter(inter_x, inter_y, s=150, c='blue', marker='o', label='Route', zorder=4)

# End hold (red)
plt.scatter(end_x, end_y, s=200, c='red', marker='*', label='Top', zorder=5)

# Draw route path
plt.plot(route_x, route_y, 'k--', linewidth=2, alpha=0.6)

plt.title("Route With Highlighted Holds")
plt.xlabel("X")
plt.ylabel("Y")
plt.gca()
plt.legend()

plt.show()