import traci
import random

# Simula la lectura de un sensor real
def get_insertion_density():
    # Densidad aleatoria entre 100 y 300 veh/hora
    return random.randint(100, 300)

sumoCmd = ["sumo", "-c", "osm.sumocfg", ]
traci.start(sumoCmd)

step = 0
while step < 3600:
    traci.simulationStep()

    # Cada 60 segundos simulados, ajustar la densidad
    if step % 60 == 0:
        density = get_insertion_density()
        vehicles_per_min = int(density / 60)
        print(f"[t={step}s] Densidad={density} veh/h → {vehicles_per_min} veh/min")

        # Añadir vehículos según la densidad actual
        for i in range(vehicles_per_min):
            vid = f"veh_{step}_{i}"
            traci.vehicle.add(vid, "pt_bus_121:0", typeID="veh_passenger")

    step += 1

traci.close()
