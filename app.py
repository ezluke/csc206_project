from flask import Flask, render_template, url_for, jsonify, redirect
from queries import (
    get_vehicles,
    get_parts,
    get_vehicle_by_id,
    get_vehicle_details,
    get_part_by_id,
    insert_vehicle_full,
    insert_part,
    get_manufacturers,
    get_vehicle_types,
    get_colors,
    filter_data,
    get_sales_productivity,
    get_seller_history,
    get_part_statistics,
)

app = Flask(__name__)


@app.route('/')
def home():
    # Route the home page to the cars listing (shows the cars table)
    return redirect(url_for('cars'))


@app.route('/cars')
def cars():
    from flask import request

    # Read possible search filters from query string
    manufacturer_id_raw = request.args.get('manufacturer_id')
    vehicle_type_id_raw = request.args.get('vehicle_type_id')
    model_year_raw = request.args.get('model_year')
    fuel_type_raw = request.args.get('fuel_type')
    color_id_raw = request.args.get('color_id')

    # Build a filters dict for the query layer (convert to ints where appropriate)
    filters = {}
    try:
        if manufacturer_id_raw:
            filters['manufacturer_id'] = int(manufacturer_id_raw)
    except ValueError:
        pass
    try:
        if vehicle_type_id_raw:
            filters['vehicle_type_id'] = int(vehicle_type_id_raw)
    except ValueError:
        pass
    try:
        if model_year_raw:
            filters['model_year'] = int(model_year_raw)
    except ValueError:
        pass
    if fuel_type_raw:
        filters['fuel_type'] = fuel_type_raw
    try:
        if color_id_raw:
            filters['color_id'] = int(color_id_raw)
    except ValueError:
        pass

    cars = get_vehicles(filters if filters else None)

    filters = filter_data()
    # Provide dropdown values and echo-filter values for the template
    manufacturers = get_manufacturers()
    vehicle_types = get_vehicle_types()
    colors = get_colors()
    current_filters = {
        'manufacturer_id': manufacturer_id_raw or '',
        'vehicle_type_id': vehicle_type_id_raw or '',
        'model_year': model_year_raw or '',
        'fuel_type': fuel_type_raw or '',
        'color_id': color_id_raw or '',
    }

    return render_template('cars/index.html', products=cars, manufacturers=filters['manufacturers'], vehicle_types=filters["vehicle_types"], colors=filters['colors'], model_year=filters['model_years'], fuel_types=filters['fuel_types'], current_filters=current_filters)


@app.route('/parts')
def parts():
    parts = get_parts()
    return render_template('parts/index.html', products=parts)


@app.route('/reports/sales-productivity')
def sales_productivity_report():
    rows = get_sales_productivity()
    return render_template('reports/sales_productivity.html', rows=rows)


@app.route('/reports/seller-history')
def seller_history_report():
    rows = get_seller_history()
    return render_template('reports/seller_history.html', rows=rows)


@app.route('/reports/part-statistics')
def part_statistics_report():
    rows = get_part_statistics()
    return render_template('reports/part_statistics.html', rows=rows)


@app.route('/car/<int:car_id>')
def car_detail(car_id):
    # Use enriched vehicle details (colors aggregated, parts cost, sales price)
    car = get_vehicle_details(car_id)
    if not car:
        return "Car not found", 404
    # Render car-specific detail template (now under cars/ folder)
    return render_template('cars/detail.html', car=car, back_url=url_for('cars'))


@app.route('/part/<int:part_id>')
def part_detail(part_id):
    part = get_part_by_id(part_id)
    if not part:
        return "Part not found", 404
    product = {
        'id': part.get('partID'),
        'name': part.get('part_number'),
        'price': part.get('cost'),
        'image': part.get('image') if 'image' in part else 'car.jpg',
        'description': part.get('description'),
        'quantity': part.get('quantity'),
        'status': part.get('status'),
    }
    return render_template('parts/detail.html', product=product, back_url=url_for('parts'))


@app.route('/login')
def login_page():
    return render_template('auth/login.html')


@app.route('/register')
def register_page():
    return render_template('auth/register.html')


@app.route('/cars/sell', methods=['GET', 'POST'])
def sell_car():
    from flask import request, redirect
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        model_year = request.form.get('model_year') or None
        description = request.form.get('description') or None
        vin = request.form.get('vin') or None
        mileage = request.form.get('mileage') or None
        fuel_type = request.form.get('fuel_type') or None
        manufacturer_id = request.form.get('manufacturer_id') or None
        vehicle_type_id = request.form.get('vehicle_type_id') or None
        price = request.form.get('price') or None
        # Insert vehicle
        vid = insert_vehicle_full(
            vin or '',
            float(mileage) if mileage else None,
            model_name,
            int(model_year) if model_year else None,
            fuel_type,
            int(manufacturer_id) if manufacturer_id else None,
            int(vehicle_type_id) if vehicle_type_id else None,
            description,
        )
        # Optionally, insert a purchasetransactions record if price provided
        if price:
            try:
                from db import get_connection
                conn = get_connection()
                cur = conn.cursor()
                cur.execute('INSERT INTO purchasetransactions (vehicleID, userID, customerID, purchase_price, purchase_date, vehicle_condition) VALUES (%s, %s, %s, %s, CURRENT_DATE(), %s)', (vid, 1, 1, float(price), 'Good'))
                conn.commit()
                cur.close()
                conn.close()
            except Exception:
                # ignore if table missing or insert fails
                pass
    return render_template('sell/sell_success.html', message='Car listed for sale!')
    # GET: provide dropdown values for manufacturers and vehicle types
    manufacturers = get_manufacturers()
    vehicle_types = get_vehicle_types()
    return render_template('sell/sell_car.html', manufacturers=manufacturers, vehicle_types=vehicle_types)


@app.route('/parts/sell', methods=['GET', 'POST'])
def sell_part():
    from flask import request
    if request.method == 'POST':
        part_number = request.form.get('part_number')
        description = request.form.get('description') or None
        cost = request.form.get('cost') or None
        quantity = request.form.get('quantity') or None
        pid = insert_part(part_number, description, float(cost) if cost else None, int(quantity) if quantity else None)
    return render_template('sell/sell_success.html', message='Part listed for sale!')
    return render_template('sell/sell_part.html')


if __name__ == '__main__':
    app.run(debug=True)