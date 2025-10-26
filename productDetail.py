from jinja2 import Template

product_detail_template = Template("""
<div class="container">
    <a href="{{ back_url }}" class="button is-primary mb-4">
        ← 
    </a>
    <div class="columns">
        <div class="column is-half">
            <figure class="image">
                <img src="{{ product.image }}" alt="{{ product.name }}">
            </figure>
        </div>
        <div class="column is-half">
            <h1 class="title is-2">{{ product.name }}</h1>
            <h2 class="subtitle is-3">${{ product.price }}</h2>
            <div class="content">
                <p>{{ product.description }}</p>
            </div>
            <button class="button is-primary is-large">Buy Now</button>
        </div>
    </div>
</div>
""")
