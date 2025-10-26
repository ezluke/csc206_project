from jinja2 import Template

product_table_template = Template("""
<div class="columns is-multiline">
    {% for product in products %}
    <div class="column is-one-third">
        <a href="/{{ product_type }}/{{ product.id }}">
            <div class="card">
                <div class="card-image">
                    <figure class="image is-4by3">
                        <img src="{{ product.image }}" alt="{{ product.name }}">
                    </figure>
                </div>
                <div class="card-content">
                    <p class="title is-4">{{ product.name }}</p>
                    <p class="subtitle is-5">${{ product.price }}</p>
                </div>
            </div>
        </a>
    </div>
    {% endfor %}
</div>
""")
