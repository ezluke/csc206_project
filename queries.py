from db import get_connection


def execute_sql(query: str, params: tuple = ()):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results



def execute_write(query: str, params: tuple = ()): 
    """Execute INSERT/UPDATE/DELETE and commit; returns lastrowid."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last = cursor.lastrowid
    cursor.close()
    conn.close()
    return last

def filter_data():
    """Return distinct values for UI filters: manufacturers, vehicle types, model years, fuel types, colors.

    Returns a dict with keys: manufacturers, vehicle_types, model_years, fuel_types, colors.
    Each value is the result of a small SELECT query suitable for populating dropdowns.
    """
    manufacturers = execute_sql("SELECT manufacturerID, manufacturer_name FROM manufacturers ORDER BY manufacturer_name;")
    vehicle_types = execute_sql("SELECT vehicle_typeID, vehicle_type_name FROM vehicletypes ORDER BY vehicle_type_name;")
    # model years — distinct values from vehicles
    model_years_rows = execute_sql("SELECT DISTINCT model_year FROM vehicles WHERE model_year IS NOT NULL ORDER BY model_year DESC;")
    # extract scalar list of years
    model_years = [r.get('model_year') for r in model_years_rows]
    # fuel types — distinct values from vehicles
    fuel_rows = execute_sql("SELECT DISTINCT fuel_type FROM vehicles WHERE fuel_type IS NOT NULL ORDER BY fuel_type;")
    fuel_types = [r.get('fuel_type') for r in fuel_rows]
    colors = execute_sql("SELECT colorID, color_name FROM colors ORDER BY color_name;")

    return {
        'manufacturers': manufacturers,
        'vehicle_types': vehicle_types,
        'model_years': model_years,
        'fuel_types': fuel_types,
        'colors': colors,
    }
    
def get_tables():
    return execute_sql("SHOW TABLES;")


def get_parts():
    return execute_sql("SELECT * FROM parts;")


def get_vehicle_by_id(vehicle_id: int):
    results = execute_sql("SELECT * FROM vehicles WHERE vehicleID = %s", (vehicle_id,))
    return results[0] if results else None


def get_vehicle_details(vehicle_id: int):
    """Return a single vehicle row enriched with manufacturer and vehicle type names,
    concatenated colors, purchase price, parts cost and computed sales_price.
    """
    query = (
        "SELECT v.vehicleID, v.vin, v.mileage, v.description, v.model_name, v.model_year, v.fuel_type, "
        "v.manufacturerID, m.manufacturer_name, v.vehicle_typeID, vt.vehicle_type_name, "
        "GROUP_CONCAT(DISTINCT c.color_name ORDER BY c.color_name SEPARATOR ', ') AS colors, "
        "pt.purchase_price AS purchase_price, "
        "COALESCE(SUM(p.cost * p.quantity), 0) AS parts_cost, "
        "CASE WHEN pt.purchase_price IS NOT NULL THEN ROUND(1.4 * pt.purchase_price + 1.2 * COALESCE(SUM(p.cost * p.quantity),0), 2) ELSE NULL END AS sales_price "
        "FROM vehicles v "
        "LEFT JOIN manufacturers m ON v.manufacturerID = m.manufacturerID "
        "LEFT JOIN vehicletypes vt ON v.vehicle_typeID = vt.vehicle_typeID "
        "LEFT JOIN vehiclecolors vc ON vc.vehicleID = v.vehicleID "
        "LEFT JOIN colors c ON vc.colorID = c.colorID "
        "LEFT JOIN purchasetransactions pt ON pt.vehicleID = v.vehicleID "
        "LEFT JOIN partorders po ON po.vehicleID = v.vehicleID "
        "LEFT JOIN parts p ON p.part_orderID = po.part_orderID "
        "WHERE v.vehicleID = %s "
        "GROUP BY v.vehicleID, v.vin, v.mileage, v.description, v.model_name, v.model_year, v.fuel_type, v.manufacturerID, m.manufacturer_name, v.vehicle_typeID, vt.vehicle_type_name, pt.purchase_price "
    )
    results = execute_sql(query, (vehicle_id,))
    return results[0] if results else None


def get_part_by_id(part_id: int):
    results = execute_sql("SELECT * FROM parts WHERE partID = %s", (part_id,))
    return results[0] if results else None


def insert_vehicle(model_name: str, model_year: int | None, description: str | None, vin: str | None):
    # insert minimal vehicle record; return inserted vehicleID
    # older minimal insert kept for backward compatibility is replaced by fuller insert
    # vehicles table columns (per schema): vin, mileage, description, model_name, model_year, fuel_type, manufacturerID, vehicle_typeID
    # This function will insert the full set where available. To preserve a simple call-site, keep the
    # same parameter order but accept additional optional parameters via keyword-only args.
    raise RuntimeError("Use insert_vehicle_full with explicit fields: vin, mileage, model_name, model_year, fuel_type, manufacturer_id, vehicle_type_id, description")


def insert_vehicle_full(vin: str, mileage: float | None, model_name: str, model_year: int | None, fuel_type: str | None, manufacturer_id: int | None, vehicle_type_id: int | None, description: str | None):
    query = "INSERT INTO vehicles (vin, mileage, description, model_name, model_year, fuel_type, manufacturerID, vehicle_typeID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    return execute_write(query, (vin, mileage, description, model_name, model_year, fuel_type, manufacturer_id, vehicle_type_id))


def insert_part(part_number: str, description: str | None, cost: float | None, quantity: int | None):
    query = "INSERT INTO parts (part_number, description, cost, quantity) VALUES (%s, %s, %s, %s)"
    return execute_write(query, (part_number, description, cost, quantity))

def get_users():
    return execute_sql("SELECT * FROM users;")

def get_vehicles(filters: dict | None = None):
    """
    Return vehicle rows enriched with manufacturer and vehicle type names for display.

    If `filters` is provided (a dict), it may contain any of:
      - manufacturer_id (int)
      - vehicle_type_id (int)
      - model_year (int)
      - fuel_type (str)
      - color_id (int) or color_name (str)

    Only sellable vehicles are returned (not sold and no outstanding parts orders).
    """
    where_clauses = [
        "NOT EXISTS (SELECT 1 FROM salestransactions s WHERE s.vehicleID = v.vehicleID)",
        "NOT EXISTS (SELECT 1 FROM partorders po JOIN parts p ON p.part_orderID = po.part_orderID WHERE po.vehicleID = v.vehicleID AND COALESCE(p.status,'') <> 'Installed')",
    ]
    params: list = []

    if filters:
        # manufacturer filter
        mid = filters.get('manufacturer_id')
        if mid:
            where_clauses.append('v.manufacturerID = %s')
            params.append(mid)
        # vehicle type filter
        vt = filters.get('vehicle_type_id')
        if vt:
            where_clauses.append('v.vehicle_typeID = %s')
            params.append(vt)
        # model year filter (exact match)
        my = filters.get('model_year')
        if my:
            where_clauses.append('v.model_year = %s')
            params.append(my)
        # fuel type filter
        ft = filters.get('fuel_type')
        if ft:
            where_clauses.append('v.fuel_type = %s')
            params.append(ft)
        # color filter - allow either id or name
        color_id = filters.get('color_id')
        color_name = filters.get('color_name')
        if color_id:
            where_clauses.append('EXISTS (SELECT 1 FROM vehiclecolors vc WHERE vc.vehicleID = v.vehicleID AND vc.colorID = %s)')
            params.append(color_id)
        elif color_name:
            where_clauses.append("EXISTS (SELECT 1 FROM vehiclecolors vc JOIN colors c ON vc.colorID = c.colorID WHERE vc.vehicleID = v.vehicleID AND c.color_name = %s)")
            params.append(color_name)

    where_sql = (' WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    # Aggregate colors (concatenate multi-colors into a single field) and compute
    # parts cost and sales price. Sales price = 140% of purchase price + 120% of parts cost.
    # Use LEFT JOINs so vehicles without purchase records still appear (sales_price NULL).
    query = (
        "SELECT v.vehicleID, v.vin, v.mileage, v.description, v.model_name, v.model_year, v.fuel_type, "
        "v.manufacturerID, m.manufacturer_name, v.vehicle_typeID, vt.vehicle_type_name, "
        "GROUP_CONCAT(DISTINCT c.color_name ORDER BY c.color_name SEPARATOR ', ') AS colors, "
        "pt.purchase_price AS purchase_price, "
        "COALESCE(SUM(p.cost * p.quantity), 0) AS parts_cost, "
        "CASE WHEN pt.purchase_price IS NOT NULL THEN ROUND(1.4 * pt.purchase_price + 1.2 * COALESCE(SUM(p.cost * p.quantity),0), 2) ELSE NULL END AS sales_price "
        "FROM vehicles v "
        "LEFT JOIN manufacturers m ON v.manufacturerID = m.manufacturerID "
        "LEFT JOIN vehicletypes vt ON v.vehicle_typeID = vt.vehicle_typeID "
        "LEFT JOIN vehiclecolors vc ON vc.vehicleID = v.vehicleID "
        "LEFT JOIN colors c ON vc.colorID = c.colorID "
        "LEFT JOIN purchasetransactions pt ON pt.vehicleID = v.vehicleID "
        "LEFT JOIN partorders po ON po.vehicleID = v.vehicleID "
        "LEFT JOIN parts p ON p.part_orderID = po.part_orderID "
        + where_sql +
    " GROUP BY v.vehicleID, v.vin, v.mileage, v.description, v.model_name, v.model_year, v.fuel_type, v.manufacturerID, m.manufacturer_name, v.vehicle_typeID, vt.vehicle_type_name, pt.purchase_price "
    "ORDER BY v.model_year DESC, m.manufacturer_name ASC;"
    )

    return execute_sql(query, tuple(params))


def get_manufacturers():
    return execute_sql("SELECT * FROM manufacturers ORDER BY manufacturer_name;")


def get_vehicle_types():
    return execute_sql("SELECT * FROM vehicletypes ORDER BY vehicle_type_name;")


def get_colors():
    return execute_sql("SELECT * FROM colors ORDER BY color_name;")


def get_sales_productivity():
    """Sales Productivity: salesperson, number vehicles sold, total selling prices, avg sale price."""
    query = (
        "SELECT u.userID, CONCAT(u.first_name, ' ', u.last_name) AS salesperson, "
        "COUNT(s.vehicleID) AS vehicles_sold, COALESCE(SUM(pt.purchase_price),0) AS total_sold_price, "
        "CASE WHEN COUNT(s.vehicleID) > 0 THEN COALESCE(SUM(pt.purchase_price),0)/COUNT(s.vehicleID) ELSE NULL END AS avg_sale_price "
        "FROM salestransactions s "
        "JOIN users u ON s.userID = u.userID "
        "LEFT JOIN purchasetransactions pt ON s.vehicleID = pt.vehicleID "
        "GROUP BY u.userID, u.first_name, u.last_name "
        "ORDER BY vehicles_sold DESC, total_sold_price DESC;"
    )
    return execute_sql(query)


def get_seller_history():
    """Seller History: sellers (customers) and number of vehicles sold to dealer and total paid."""
    query = (
        "SELECT c.customerID, CONCAT(c.first_name, ' ', c.last_name) AS seller_name, "
        "COUNT(pt.vehicleID) AS vehicles_sold_to_dealer, COALESCE(SUM(pt.purchase_price),0) AS total_paid "
        "FROM purchasetransactions pt "
        "JOIN customers c ON pt.customerID = c.customerID "
        "GROUP BY c.customerID, c.first_name, c.last_name "
        "ORDER BY vehicles_sold_to_dealer DESC, total_paid ASC;"
    )
    return execute_sql(query)


def get_part_statistics():
    """Part statistics per vendor: total parts purchased (sum quantity), total spent, avg cost per unit."""
    query = (
        "SELECT v.vendorID, v.vendor_name, COALESCE(SUM(p.quantity),0) AS parts_purchased, "
        "COALESCE(SUM(p.cost * p.quantity),0.00) AS total_spent, "
        "CASE WHEN SUM(p.quantity) > 0 THEN SUM(p.cost * p.quantity)/SUM(p.quantity) ELSE NULL END AS avg_cost_per_part "
        "FROM partorders po "
        "JOIN vendors v ON po.vendorID = v.vendorID "
        "JOIN parts p ON p.part_orderID = po.part_orderID "
        "GROUP BY v.vendorID, v.vendor_name "
        "ORDER BY parts_purchased DESC;"
    )
    return execute_sql(query)

