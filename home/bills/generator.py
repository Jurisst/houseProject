import os
import re


# for file and url creation
# models_list = ['house', 'consumer', 'apartment', 'meter', 'service', 'provider']
models_list = ['service', 'provider']


def create_html_file(directory: str, filename: str,
                     content: str = "<h1>Success!</h1><p>Service has been saved</p><a href='/bills/add_service'>Add another service</a>"):
    """
    Creates an HTML file with the specified name in the specified directory.

    :param directory: The directory where the HTML file should be created.
    :param filename: The name of the HTML file (should end with .html).
    :param content: The default HTML content to be written to the file.
    """
    if not filename.endswith(".html"):
        raise ValueError("Filename must have a .html extension")

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Define the full file path
    file_path = os.path.join(directory, filename)

    # Write content to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"HTML file created at: {file_path}")
    return file_path


for mod in models_list:
    n_string = "apartment_list.html"
    a_string = """
{% extends 'base.html' %}
{% block title %} Add apartment {% endblock %}
{% block sidebar %}
<aside class="vertical-menu">
    {% if house.id %}
        <a href="{% url 'apartments_by_house' house.id %}">Back to house's apartments</a>
    {% else %}
        <a href="{% url 'apartments' %}">Back to apartments</a>
    {% endif %}
    <a href="#">Profile</a>
    <a href="#">Settings</a>
    <a href="#">Logout</a>
</aside>
{% endblock %}
{% block content %}
<form method="post">
  {% csrf_token %}
    {% if house %}
    <h1>Add Apartment for {{ house }}</h1>>
    {% else %}
    <h1>Add New apartment</h1>>
    {% endif %}
  {{ form.as_p }}
  <button type="submit">Add Apartment</button>
</form>
  {% if err %}
    <div id="error" style="border: blue 2px solid; background-color: #E62600; color:white; display: inline-block">{{err|safe}}</div>
  {% endif %}
{% endblock %}
"""
    # a_string = a_string.replace('service', mod)

    n_string = n_string.replace('apartment', mod)
    a_string = a_string.replace('apartment', mod)
    a_string = a_string.replace('Apartment', mod.capitalize())

    create_html_file("./templates_t", n_string, a_string)