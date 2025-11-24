from flask import Flask, render_template_string, session
from app import app

def test_render():
    with app.test_request_context('/'):
        # Simulate Buyer session
        session['role'] = 'Buyer'
        parts = [{'part_number': '123', 'description': 'Test Part', 'vendor_name': 'Test Vendor', 'status': 'Ordered'}]
        
        template = """
        {% if session.get('role') in ['Owner', 'Buyer'] %}
            PARTS_VISIBLE
        {% else %}
            PARTS_HIDDEN
        {% endif %}
        """
        
        rendered = render_template_string(template, parts=parts)
        print(f"Role: Buyer, Result: {rendered.strip()}")

        # Simulate Owner session
        session['role'] = 'Owner'
        rendered = render_template_string(template, parts=parts)
        print(f"Role: Owner, Result: {rendered.strip()}")

        # Simulate Sales session
        session['role'] = 'Sales'
        rendered = render_template_string(template, parts=parts)
        print(f"Role: Sales, Result: {rendered.strip()}")

if __name__ == "__main__":
    test_render()