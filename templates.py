INNER_TEMPLATE_STR = '''
{{ plot_script }}
<button class="accordion">
  {{ grade }}
</button>
<div class="panel">
<div class="row">
    <div class="grid-large-third">
        {{ plot_div["barchart"] }}
    </div>
    <div class="grid-large-third">
        {{ plot_div["donut"] }}
    </div>
    <div class="grid-small-slice color-box">
        {{ plot_div["total_hours"] }}
    </div>
</div>
<div class="row">
    <div class="grid-full">
        {{ plot_div["days"] }}
        {{ plot_div["slider"] }}
    </div>
</div>
{% if plot_div["curricula"] or plot_div["reading_level"] %}
    <div class="row">
        {% if plot_div["curricula"] %}
            <div class="grid-half">
                {{ plot_div["curricula"] }}
            </div>
        {% endif %}
        {% if plot_div["reading_level"] %}
            <div class="grid-half">
                {{ plot_div["reading_level"] }}
            </div>
        {% endif %}
    </div>
{% endif %}
<div class="row">
    {% for i in range(dyn_scripts|length) %}
        {% if i is even  %}
            {{ dyn_scripts[i] }}
            {{ dyn_scripts[i+1] }}
            <div class="grid-half">
                {{ dyn_divs[i] }}
                {{ dyn_divs[i+1] }}
            </div>
        {% endif %}
    {% endfor %}
</div>
</div>
'''

OUTER_TEMPLATE_STR = '''<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Homeschool Dashboard</title>
        {{ bokeh_js }}
        {{ bokeh_css }}
        <style>
            {{css}}
        </style>
    </head>
    <body>
        <header>
            {{ name_script }}
            {{ name }}
        </header>
        <div class="main-wrapper">
            {{ content }}
        </div>
        <script>
          var acc = document.getElementsByClassName("accordion");
          var i;

          for (i = 0; i < acc.length; i++) {
            acc[i].addEventListener("click", function() {
              this.classList.toggle("active");
              var panel = this.nextElementSibling;
              panel.classList.toggle("active-panel");
              if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
              } else {
                //panel.style.maxHeight = panel.scrollHeight + "px";
              }
            });
          }
        </script>
    </body>
</html>
'''
