import os
models_list = ['house', 'consumer', 'apartment', 'meter']

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
    n_string = "add_service.html"
    a_string = """r"<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Add Provider</button>
</form>
  {% if err %}
    <div id="error" style="border: blue 2px solid; background-color: #E62600; color:white; display: inline-block">{{err|safe}}</div>
  {% endif %}"
  """

    # Example usage


    # a_string = a_string.replace('service', mod)
    n_string = n_string.replace('service', mod)
    a_string = a_string.replace('Provider', mod.capitalize())

    create_html_file("./templates_t", n_string, a_string)
