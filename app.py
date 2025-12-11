from flask import Flask, render_template, url_for, jsonify, redirect, render_template_string, request, session
from datetime import timedelta, date
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
    authenticate_user,
    add_user,
    get_vehicle_parts,
    get_vehicle_transactions,
    update_part_status,
    get_customers,
    add_customer
)






app = Flask(__name__)

app.secret_key = 'BAD_SECRET_KEY'
app.permanent_session_lifetime = timedelta(minutes=60)

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
    get_all_raw = request.args.get('get_all')

    if get_all_raw == None or get_all_raw == '0':
        get_all_raw = False
    else:
        get_all_raw = True

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

    cars = get_vehicles(filters if filters else None, get_all_raw)
    
    role = session.get('role')
    if role == 'Owner':
        cars = get_vehicles(filters if filters else None, True)
    elif role == 'Buyer':
        cars = get_vehicles(filters if filters else None, False, True)

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
    
    # Fetch additional data based on role
    # Always fetch parts, let template decide visibility
    parts = get_vehicle_parts(car_id)
    
    transactions = None
    role = session.get('role')
        
    if role == 'Owner':
        transactions = get_vehicle_transactions(car_id)

    # Render car-specific detail template (now under cars/ folder)
    return render_template('cars/detail.html', car=car, parts=parts, transactions=transactions, back_url=url_for('cars'))


@app.route('/car/<int:car_id>/sell', methods=['GET', 'POST'])
def sell_vehicle(car_id):
    if session.get('role') not in ['Sales', 'Owner']:
        return "Unauthorized", 403
        
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        sales_date = request.form.get('sales_date')
        user_id = session.get('user_id')
        
        if customer_id and sales_date and user_id:
            try:
                from db import get_connection
                conn = get_connection()
                cur = conn.cursor()
                cur.execute('INSERT INTO salestransactions (vehicleID, userID, customerID, sales_date) VALUES (%s, %s, %s, %s)', (car_id, user_id, customer_id, sales_date))
                conn.commit()
                cur.close()
                conn.close()
                return render_template('sell/sell_success.html', message='Vehicle sold successfully!')
            except Exception as e:
                return f"Error selling vehicle: {e}", 500
                
    car = get_vehicle_details(car_id)
    customers = get_customers()
    new_customer_id = request.args.get('new_customer_id')
    return render_template('cars/sell_to_customer.html', car=car, customers=customers, today=date.today(), new_customer_id=new_customer_id)


@app.route('/part/<int:part_id>/install', methods=['POST'])
def install_part(part_id):
    if session.get('role') not in ['Buyer', 'Owner']:
        return "Unauthorized", 403
    
    update_part_status(part_id, 'Installed')
    # Redirect back to the referring page (the car detail page)
    return redirect(request.referrer or url_for('cars'))


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




@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == 'POST':

        #test to see if user is in database
        email = request.form.get('email_address')
        password = request.form.get('password')

        if not email or not password:
            error = "Please enter both email and password."
        else:
            user = authenticate_user(email, password)

            if user:
                # Create a permanent session (True)
                session.permanent = False
                # Save the form data to the session object
                session['email'] = request.form['email_address']
                session['user_id'] = user.get('userID')
                session['name'] = f"{user.get('first_name')} {user.get('last_name')}"
                role = user.get('role')
                session['role'] = role.strip() if role else None
                return redirect('/')
            else:
                error = "Invalid email or password."
            
    return render_template('auth/login.html', error=error)




@app.route('/register', methods=['GET', 'POST'])
def register_page():
    error = None
    if request.method == 'POST':

        #test to see if user is in database
        email = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        if not email or not password or not first_name or not last_name:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            try:
                user_id = add_user(email, password, 'Sales', first_name, last_name)
                if user_id:
                    # Create a permanent session (True)
                    session.permanent = False
                    # Save the form data to the session object
                    session['email'] = email
                    session['user_id'] = user_id
                    return redirect('/')
                else:
                    error = "Registration failed. Please try again."
            except Exception as e:
                # Likely a duplicate username or database error
                print(f"Registration error: {e}")
                error = "Username already exists or database error occurred."

    return render_template('auth/register.html', error=error)


@app.route('/customers/new', methods=['GET', 'POST'])
def create_customer():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        id_number = request.form.get('id_number')
        
        try:
            cid = add_customer(first_name, last_name, email, phone, street, city, state, zip_code, id_number)
            # Redirect to the referrer with the new customer ID
            referrer = request.referrer
            if referrer and '?' in referrer:
                 return redirect(referrer + f"&new_customer_id={cid}")
            elif referrer:
                 return redirect(referrer + f"?new_customer_id={cid}")
            return redirect(url_for('sell_car', new_customer_id=cid))
        except Exception as e:
            return f"Error creating customer: {e}", 500
            
    return render_template('customers/create.html')


@app.route('/cars/sell', methods=['GET', 'POST'])
def sell_car():
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
        customer_id = request.form.get('customer_id')
        condition = request.form.get('condition')
        user_id = session.get('user_id')

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
        if price and customer_id and user_id:
            try:
                from db import get_connection
                conn = get_connection()
                cur = conn.cursor()
                cur.execute('INSERT INTO purchasetransactions (vehicleID, userID, customerID, purchase_price, purchase_date, vehicle_condition) VALUES (%s, %s, %s, %s, CURRENT_DATE(), %s)', (vid, user_id, customer_id, float(price), condition))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Error inserting purchase transaction: {e}")
                pass
        return render_template('sell/sell_success.html', message='Car listed for sale!')
    
    # GET: provide dropdown values for manufacturers and vehicle types
    manufacturers = get_manufacturers()
    vehicle_types = get_vehicle_types()
    customers = get_customers()
    filters = filter_data()
    fuel_types = filters['fuel_types']
    new_customer_id = request.args.get('new_customer_id')
    return render_template('sell/sell_car.html', manufacturers=manufacturers, vehicle_types=vehicle_types, customers=customers, fuel_types=fuel_types, new_customer_id=new_customer_id)


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


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)