from queries import get_vehicle_parts, get_vehicle_by_id

def debug_parts():
    # Check vehicle 92 (from logs)
    vid = 92
    print(f"--- Checking Vehicle {vid} ---")
    vehicle = get_vehicle_by_id(vid)
    if vehicle:
        print(f"Vehicle found: {vehicle['model_year']} {vehicle['model_name']}")
    else:
        print("Vehicle NOT found")
        
    parts = get_vehicle_parts(vid)
    print(f"Parts count: {len(parts)}")
    for p in parts:
        print(p)

    # Check a vehicle that definitely has parts (e.g. vehicleID 2 from partorders insert)
    # INSERT INTO `csc206cars`.`partorders` ... VALUES (9, 1, 2, 1) -> Vehicle 2 has parts
    vid = 2
    print(f"\n--- Checking Vehicle {vid} ---")
    vehicle = get_vehicle_by_id(vid)
    if vehicle:
        print(f"Vehicle found: {vehicle['model_year']} {vehicle['model_name']}")
    else:
        print("Vehicle NOT found")

    parts = get_vehicle_parts(vid)
    print(f"Parts count: {len(parts)}")
    for p in parts:
        print(p)

    # Check vehicle 11 (from logs)
    vid = 11
    print(f"\n--- Checking Vehicle {vid} ---")
    vehicle = get_vehicle_by_id(vid)
    if vehicle:
        print(f"Vehicle found: {vehicle['model_year']} {vehicle['model_name']}")
    else:
        print("Vehicle NOT found")

    parts = get_vehicle_parts(vid)
    print(f"Parts count: {len(parts)}")
    for p in parts:
        print(p)

if __name__ == "__main__":
    debug_parts()