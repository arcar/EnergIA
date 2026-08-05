import json


class DispatchService:

    def __init__(self, json_path, dijkstra_service):

        self.dijkstra_service = dijkstra_service

        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.plants = data["plants"]

    def plants_by_region(
        self,
        region,
        destination=None,
        timestep_minutes=15
):

        plants = self.available_plants(
            destination,
            timestep_minutes
        )

        return [
            plant
            for plant in plants
            if plant["region"] == region
        ]
    def find_candidates(
        self,
        destination,
        region=None,
        timestep_minutes=15
):

        if region:

            local = self.plants_by_region(
                region,
                destination,
                timestep_minutes
            )

            if local:
                return local


        return self.available_plants(
            destination,
            timestep_minutes
        )

    def available_plants(self, destination=None, timestep_minutes=15):

        plants = []

        for plant in self.plants:

            # Une centrale ne peut pas alimenter son propre besoin
            if plant["id"] == destination:
                continue

            simulation = plant.get("simulation", {})

            margin = simulation.get(
                "initial_dispatchable_margin_mw",
                0
            )

            ramp = simulation.get(
                "max_ramp_up_mw_per_15_min",
                margin
            )

            # Puissance réellement mobilisable sur le pas de temps
            available_power = min(
                margin,
                ramp
            )

            if available_power > 0:

                plants.append({
                    "id": plant["id"],
                    "name": plant["name"],
                    "region": plant["location"]["region_name"],
                    "available_power_mw": available_power
                })


        return plants



    def allocate_power(
        self,
        destination,
        demand_mw,
        region=None,
        timestep_minutes=15
):


        allocations = []

        remaining = demand_mw


        candidates = self.rank_candidates(
    destination,
    region,
    timestep_minutes
)


        for plant in candidates:

            if remaining <= 0:
                break

            path_capacity = self.dijkstra_service.path_capacity(
                plant["path"]
            )


            power = min(
                plant["available_power_mw"],
                path_capacity,
                remaining
            )


            limitation = "none"

            if power == plant["available_power_mw"]:
                limitation = "plant_availability"

            elif power == path_capacity:
                limitation = "network_capacity"


            allocations.append({
                "plant": plant["id"],
                "power_mw": power,
                "path": plant["path"],
                "loss_percent": plant["loss_percent"],
                "path_capacity_mw": path_capacity,
                "limitation": limitation
            })


            remaining -= power



            allocated_power = demand_mw - remaining

            remaining_power = max(
                demand_mw - allocated_power,
                0
            )


            if remaining_power == 0:
                status = "satisfied"

            elif allocated_power > 0:
                status = "partially_satisfied"

            else:
                status = "no_available_generation"



            return {
    "status": status,
    "requested_power_mw": demand_mw,
    "allocated_power_mw": allocated_power,
    "remaining_power_mw": remaining_power,
    "allocations": allocations
}



    def find_candidates(
        self,
        destination,
        region=None,
        timestep_minutes=15
):

        # 1 - Recherche locale
        if region:

            local = self.plants_by_region(
                region,
                destination,
                timestep_minutes
            )

            if local:
                return local


        # 2 - Secours national
        return self.available_plants(
            destination,
            timestep_minutes
        )


    def rank_candidates(
        self,
        destination,
        region=None,
        timestep_minutes=15
):


        ranked = []

        candidates = self.find_candidates(
    destination,
    region,
    timestep_minutes
)


        for plant in candidates:

            path = self.dijkstra_service.shortest_path(
                plant["id"],
                destination,
                weight="loss"
            )

            if path is None:
                continue

            ranked.append({
    "id": plant["id"],
    "name": plant["name"],
    "region": plant["region"],
    "origin": "local" if region and plant["region"] == region else "external",
    "available_power_mw": plant["available_power_mw"],
    "path": path["path"],
    "loss_percent": path["loss_percent"],
    "distance_km": path["distance_km"]
})



        ranked.sort(
            key=lambda x: (
                x["loss_percent"],
                x["distance_km"],
                -x["available_power_mw"]
            )
        )

        return ranked

    def path_capacity(self, path):

        max_capacity = float("inf")

        for i in range(len(path) - 1):

            source = path[i]
            destination = path[i + 1]

            for edge in self.graph[source]:

                if edge["node"] == destination:

                    max_capacity = min(
                        max_capacity,
                        edge["capacity"]
                    )

                    break

        return max_capacity


