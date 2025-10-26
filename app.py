import flask
import layout
import productTable
import productDetail
import login
import register

app = flask.Flask(__name__)

cars_data = {
    1: {"id": 1, "name": "Honda Civic", "price": 25000, "image": "/static/car.jpg", "description": "Reliable and efficient sedan perfect for daily commuting."},
    2: {"id": 2, "name": "Toyota Camry", "price": 28000, "image": "/static/car.jpg", "description": "Spacious family sedan with excellent safety features."},
    3: {"id": 3, "name": "Ford Mustang", "price": 35000, "image": "/static/car.jpg", "description": "Iconic American muscle car with powerful performance."},
    4: {"id": 4, "name": "Tesla Model 3", "price": 45000, "image": "/static/car.jpg", "description": "Electric vehicle with cutting-edge technology."},
}

parts_data = {
    1: {"id": 1, "name": "Brake Pads", "price": 50, "image": "/static/car.jpg", "description": "High-quality brake pads for safe stopping power."},
    2: {"id": 2, "name": "Oil Filter", "price": 15, "image": "/static/car.jpg", "description": "Essential oil filter for engine maintenance."},
    3: {"id": 3, "name": "Air Filter", "price": 20, "image": "/static/car.jpg", "description": "Keep your engine breathing clean air."},
    4: {"id": 4, "name": "Spark Plugs", "price": 30, "image": "/static/car.jpg", "description": "Premium spark plugs for optimal ignition."},
}

@app.route('/')
def home():
    all_products = list(cars_data.values()) + list(parts_data.values())
    content = productTable.product_table_template.render(
        products=all_products, 
        product_type='car' if all_products else ''
    )
    # Need to handle mixed product types
    cars_content = productTable.product_table_template.render(products=list(cars_data.values()), product_type='car')
    parts_content = productTable.product_table_template.render(products=list(parts_data.values()), product_type='part')
    content = f"<h2 class='title'>Cars</h2>{cars_content}<h2 class='title'>Parts</h2>{parts_content}"
    html_content = layout.header_template.render(
        title="Car Retail Home",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

@app.route('/cars')
def cars():
    content = productTable.product_table_template.render(products=list(cars_data.values()), product_type='car')
    html_content = layout.header_template.render(
        title="Cars - Car Retail",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

@app.route('/parts')
def parts():
    content = productTable.product_table_template.render(products=list(parts_data.values()), product_type='part')
    html_content = layout.header_template.render(
        title="Parts - Car Retail",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    car = cars_data.get(car_id)
    if not car:
        return "Car not found", 404
    content = productDetail.product_detail_template.render(
        product=car, 
        back_url="/cars", 
        product_type="Car"
    )
    html_content = layout.header_template.render(
        title=f"{car['name']} - Car Retail",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

@app.route('/part/<int:part_id>')
def part_detail(part_id):
    part = parts_data.get(part_id)
    if not part:
        return "Part not found", 404
    content = productDetail.product_detail_template.render(
        product=part, 
        back_url="/parts", 
        product_type="Part"
    )
    html_content = layout.header_template.render(
        title=f"{part['name']} - Car Retail",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

@app.route('/login')
def login_page():
    content = login.login_template.render()
    html_content = layout.header_template.render(
        title="Login - Car Retail",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

@app.route('/register')
def register_page():
    content = register.register_template.render()
    html_content = layout.header_template.render(
        title="Sign Up - Car Retail",
        stylesheet="/static/styles.css",
        content=content,
    )
    return html_content

if __name__ == '__main__':
    app.run(debug=True)