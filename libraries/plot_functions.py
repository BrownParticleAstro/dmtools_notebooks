import json
import base64
import io

from datetime import datetime, timezone

import logging

def get_color_mpl(color_in):
    trace_color = {}

    # Define the base color and alpha based on the input
    if color_in in ('k', 'black', 'Blk'):
        trace_color.update({'color': 'black', 'alpha': 1})
    elif color_in in ('r', 'red', 'Red', 'dkr'):
        trace_color.update({'color': 'red', 'alpha': 1})
    elif color_in in ('dkg', 'DkG', 'green', 'Grn'):
        trace_color.update({'color': 'green', 'alpha': 1})
    elif color_in in ('ltg', 'LtG'):
        trace_color.update({'color': 'green', 'alpha': 0.5})
    elif color_in in ('ltr', 'LtR'):
        trace_color.update({'color': 'red', 'alpha': 0.5})
    elif color_in == 'b':
        trace_color.update({'color': 'blue', 'alpha': 1})
    elif color_in in ('ltb', 'LtB', 'Blue','Blu','DkB'):
        trace_color.update({'color': 'blue', 'alpha': 0.5})
    elif color_in in ('c', 'Cyan', 'cyan'):
        trace_color.update({'color': 'cyan', 'alpha': 1})
    elif color_in in ('g', 'grey'):
        trace_color.update({'color': 'grey', 'alpha': 1})
    elif color_in in ('g10', 'g20', 'g30', 'g40', 'g50', 'g60', 'g70', 'g80', 'g90', 'G60'):
        trace_color.update({'color': 'grey'})
        try:
            shade = int(color_in[1:]) / 100
            trace_color.update({'alpha': shade})
        except:
            trace_color.update({'alpha': 1})
    elif color_in in ('m', 'magenta', 'Mag'):
        trace_color.update({'color': 'magenta', 'alpha': 1})
    elif color_in in ('y', 'yellow','Yel'):
        trace_color.update({'color': 'yellow', 'alpha': 1})
    elif color_in in ('w', 'white'):
        trace_color.update({'color': 'white', 'alpha': 1})
    else:
        trace_color.update({'color': 'black', 'alpha': 1})

    return trace_color

    
def get_style_mpl(color_in, style_in):
    trace_color = get_color_mpl(color_in)
    trace_style = trace_color.copy()  # Start by copying the color attributes

    # Set the style based on the style_in input
    if style_in in ('dot', 'dotted', 'Dot'):
        trace_style.update({
            'linestyle': ':',
            'linewidth': 1,
            'marker': None,
            'markersize': 0,
            'alpha': 1,
            'fill': False,
            'style': 'dot'
        })
    elif style_in in ('dash', 'Dash'):
        trace_style.update({
            'linestyle': '--',
            'linewidth': 1,
            'marker': None,
            'markersize': 0,
            'alpha': 1,
            'fill': False,
            'style': 'dash'
        })
    elif style_in in ('fill', 'Fill'):
        trace_style.update({
            'linestyle': None,
            'linewidth': 0,
            'marker': None,
            'markersize': 0,
            'alpha': 0.3,
            'fill': True,
            'style': 'fill'
        })
    elif style_in in ('Line', 'line', 'lines'):
        trace_style.update({
            'linestyle': '-',
            'linewidth': 1,
            'marker': None,
            'markersize': 0,
            'alpha': 1,
            'fill': False,
            'style': 'line'
        })
    elif style_in == "point":
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': '.',
            'markersize': 8,
            'alpha': 1,
            'fill': False,
            'style': 'point'
        })
    elif style_in in ('cross', 'Cross'):
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': 'x',
            'markersize': 8,
            'alpha': 1,
            'fill': False,
            'style': 'cross'
        })
    elif style_in == 'circle':
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': 'o',
            'markersize': 8,
            'alpha': 1,
            'fill': False,
            'style': 'circle'
        })
    elif style_in == 'plus':
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': '+',
            'markersize': 8,
            'alpha': 1,
            'fill': False,
            'style': 'plus'
        })
    elif style_in in ('asterisk', 'star'):
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': '*',
            'markersize': 12,
            'alpha': 1,
            'fill': False,
            'style': 'star'
        })
    elif style_in in ('pentagon', "pent"):
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': "p",
            'markersize': 10,
            'alpha': 1,
            'fill': False,
            'style': 'pentagon'
        })
    elif style_in in ('hex', 'hexagon'):
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': 'h',
            'markersize': 10,
            'alpha': 1,
            'fill': False,
            'style': 'hexagon'
        })
    elif style_in in ('triu', 'triangle-up'):
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': "^",
            'markersize': 10,
            'alpha': 1,
            'fill': False,
            'style': 'triangle-up'
        })
    elif style_in in ('trid', 'triangle-down'):
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': "v",
            'markersize': 10,
            'alpha': 1,
            'fill': False,
            'style': 'triangle-down'
        })
    elif style_in in ('tril','triangle-left') :
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': "<",
            'markersize': 10,
            'alpha': 1,
            'fill': False,
            'style': 'triangle-left'
        })
    elif style_in in ('trir', 'triangle-right') :
        trace_style.update({
            'linestyle': 'None',
            'linewidth': 1,
            'marker': ">",
            'markersize': 10,
            'alpha': 1,
            'fill': False,
            'style': 'triangle-right'
        })
    else:
        trace_style.update({
            'linestyle': '-',
            'linewidth': 1,
            'marker': None,
            'markersize': 0,
            'alpha': 1,
            'fill': False,
            'style': 'line'
        })

    return trace_style

def get_clean_color_style(color_in, style_in):
    
    clean_trace_dict = get_color_mpl(color_in)
    clean_trace_color = clean_trace_dict['color']

    # Set the style based on the style_in input
    if style_in in ('dot', 'dotted', 'Dot'):
        clean_trace_style = 'dotted'
    elif style_in in ('dash', 'Dash'):
        clean_trace_style = 'dash'
    elif style_in in ('fill', 'Fill'):
        clean_trace_style = 'fill'
    elif style_in in ('Line', 'line', 'lines'):
        clean_trace_style = 'line'
    elif style_in == 'point':
        clean_trace_style = 'point'
    elif style_in in ('cross', 'Cross'):
        clean_trace_style = 'cross'
    elif style_in == 'circle':
        clean_trace_style = 'circle'
    elif style_in == 'plus':
        clean_trace_style = 'cross'
    elif style_in in ('asterisk', 'star'):
        clean_trace_style = 'star'
    elif style_in in ('pentagon', 'pent'):
        clean_trace_style = 'pentagon'
    elif style_in in ('hex', 'hexagon'):
        clean_trace_style = 'hexagon'
    elif style_in in ('triu', 'triangle', 'triangle-up'):
        clean_trace_style = 'triangle-up'
    elif style_in == ('trid', 'triangle', 'triangle-down'):
        clean_trace_style = 'triangle-down'
    elif style_in == ('tril','triangle-left') :
        clean_trace_style = 'triangle-left'
    elif style_in == ('trir', 'triangle-right') :
        clean_trace_style = 'triangle-right'
    else:
        clean_trace_style = 'line'

    return clean_trace_color, clean_trace_style
    
def get_empty_plot():
    empty_plot = {
      "dmtools_current_plot": {
        "plot_node": {
          "record": {
            "id": -1,
            "type": "Plot",
            "created": "2025-07-26T14:46:37.430Z",
            "updated": "2025-07-26T14:46:37.430Z"
          },
          "properties": {
            "name": "Default Plot",
            "xMax": "100",
            "xMin": "0",
            "yMax": "100",
            "yMin": "0",
            "xUnits": "keV/c^2",
            "yUnits": "cm^2",
            "plotType": "Cross Section vs WIMP Mass"
          }
        },
        "display_data": [
          {
            "data": [
              {
                "record": {
                  "id": -1,
                  "type": "Data",
                  "created": "2025-07-26T14:46:37.430Z",
                  "updated": "2025-07-26T14:46:37.430Z"
                },
                "properties": {
                  "raw": "[[['0','0'],['0','1'],['1','1'],['1','0'],['0','0']]]",
                  "open": 0,
                  "year": 2000,
                  "label": "label",
                  "hepUrl": "https://www.hepdata.net/record/show/hepdata.123456",
                  "public": 0,
                  "rating": 0,
                  "values": [
                    [
                      ["0", "0"],
                      ["0", "1"],
                      ["1", "1"],
                      ["1", "0"],
                      ["0", "0"]
                    ]
                  ],
                  "xUnits": "GeV/c^2",
                  "yUnits": "cm2",
                  "comment": "comment",
                  "dateEnd": None,
                  "official": 0,
                  "xRescale": "1",
                  "yRescale": "1",
                  "dateStart": None,
                  "reference": "reference",
                  "experiment": "Experiment",
                  "resultType": "Th",
                  "greatestHit": 0,
                  "label_short": "label",
                  "dateOfficial": None,
                  "defaultColor": "black",
                  "defaultStyle": "line",
                  "spinDependency": "SD",
                  "measurementType": "Unknown",
                  "dateAnnouncement": None
                }
              }
            ],
            "record": {
              "id": -1,
              "type": "Display",
              "created": "2025-07-26T14:46:37.430Z",
              "updated": "2025-07-26T14:46:37.430Z"
            },
            "properties": {
              "color": "black",
              "style": "line"
            }
          }
        ]
      }
    }
    return empty_plot

## Unit scaling
## Need help when creating brand new plot and what the default scale should be?
unit_factors = {
    'eV': 1e0,
    'keV': 1e3,
    'MeV': 1e6,
    'GeV': 1e9,
    'TeV': 1e12
}

def normalize_unit(unit):
    # Remove '/c^2', '/c2', '/c²', etc. and whitespace
    #print("unit >>", unit)
    try:
        unit = unit.strip()
        if '/c' in unit:
            unit = unit.split('/c')[0]
    except:
        unit = unit

    return unit

def convert_mass_units(value, from_unit, to_unit):
    """
    Convert a mass value (or array) from one energy/c^2 unit to another.
    from_unit and to_unit can be like 'GeV', 'GeV/c^2', 'MeV/c2', etc.
    """
    from_unit_norm = normalize_unit(from_unit)
    to_unit_norm = normalize_unit(to_unit)
    #print("convert_mass_units : from ", from_unit_norm, " to ", to_unit_norm)
    if from_unit_norm not in unit_factors or to_unit_norm not in unit_factors:
        raise ValueError(f"Supported units: {list(unit_factors.keys())}")
    try:
        value_eV = value * unit_factors[from_unit_norm]
        result = value_eV / unit_factors[to_unit_norm]
    except:
        result = 0
    return result

allowed_units = ['eV', 'keV', 'MeV', 'GeV', 'TeV']

def get_x_label(selected_unit):
    selected_unit = normalize_unit(selected_unit)
    if selected_unit not in allowed_units:
        #raise ValueError(f"Unit must be one of: {allowed_units}")
        selected_unit = 'GeV'  # Default to GeV if invalid unit is provided
    return r"$\mathrm{WIMP\ Mass}\ [\mathrm{" + selected_unit + r"}/c^{2}]$"
