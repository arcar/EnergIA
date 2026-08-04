import heapq

def build_path(previous, edges, start, goal):

    path = []
    current = goal

    while current in previous:
        path.append(current)
        current = previous[current]

    path.append(start)
    path.reverse()

    if path[0] != start:
        return None

    total_loss = 0
    max_capacity = float("inf")

    for i in range(len(path)-1):

        source = path[i]
        destination = path[i+1]

        for edge in edges[source]:
            if edge["node"] == destination:
                total_loss += edge.get("loss", 0)
                max_capacity = min(max_capacity, edge.get("capacity", float("inf")))
                break

    return {
        "path": path,
        "loss_percent": round(total_loss, 2),
        "max_capacity_mw": max_capacity
    }


def dijkstra(graph, start, goal, weight="distance"):
    
    if start not in graph or goal not in graph:
        return None

    distances = {node: float("inf")
        for node in graph
    }

    distances[start] = 0

    previous = {}

    queue = [(0, start)]

    while queue:

        current_distance, current_node = heapq.heappop(queue)

        # Ignore les anciennes distances
        if current_distance > distances[current_node]:
            continue

        if current_node == goal:
            break

        for neighbor in graph[current_node]:

            # Ignore les liaisons sans capacité
            if neighbor["capacity"] <= 0:
                continue

            node = neighbor["node"]
            if weight == "distance":
                    cost = neighbor["distance"]
            
            elif weight == "loss":
                    cost = neighbor["loss"]
            
            else:
                    cost = neighbor["distance"]
            

            new_distance = current_distance + cost

            if new_distance < distances[node]:

                distances[node] = new_distance

                previous[node] = current_node

                heapq.heappush(queue, (new_distance, node))

    if distances[goal] == float("inf"):
        return None

    result = build_path(previous, graph, start, goal)
    result["distance_km"] = round(distances[goal], 2)
    
    return result

if __name__ == "__main__":

    graph = {
        "A": [{"node": "B",
                "distance": 10,
                "capacity": 100}],
        "B": [{"node": "C",
                "distance": 20,
                "capacity": 100}],
        "C": []
    }

    result = dijkstra(graph, "A", "C")

    print(result)