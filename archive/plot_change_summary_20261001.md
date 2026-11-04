# Plot Notebook Changes Summary

This file summarizes the key code changes between `current_plot_modular_20260928.ipynb` and `new_plot_modular_20261001.ipynb`.

## 1. `get_current_plots_data` was generalized

Before:

```python
def get_current_plots_data():
    r_51_len = len(r_51)
    # ... used hardcoded r_51 and r_52
```

After:

```python
def get_current_plots_data(dataset1, dataset2=None):
    length = len(dataset1)
    first_data = 0
    record = dataset1[first_data]['record']
    properties = dataset1[first_data]['properties']
    if dataset2 != None:
      record2 = r_52[first_data]['record']
      properties2 = r_52[first_data]['properties']
```

### Impact
- The function is now parameterized and reusable with arbitrary datasets.
- It supports optional second dataset input for comparison plots.

## 2. Plot axis ranges changed

Before:

```python
plot_framework['dmtools_current_plot']['plot_node']['properties']['yMax'] = -26
plot_framework['dmtools_current_plot']['plot_node']['properties']['yMin'] = -54
plot_framework['dmtools_current_plot']['plot_node']['properties']['xMax'] = 10000
plot_framework['dmtools_current_plot']['plot_node']['properties']['xMin'] = 1
```

After:

```python
plot_framework['dmtools_current_plot']['plot_node']['properties']['yMax'] = -44
plot_framework['dmtools_current_plot']['plot_node']['properties']['yMin'] = -48
plot_framework['dmtools_current_plot']['plot_node']['properties']['xMax'] = 10500
plot_framework['dmtools_current_plot']['plot_node']['properties']['xMin'] = 10
```

### Impact
- New bounds focus on a narrower, more relevant region for the current data.
- The displayed mass range and cross-section range were adjusted for better plot readability.

## 3. New LZ data was added

New cells were added with LZ results, including:

- `LZ_2026`
- `LZ_2025`

These datasets were introduced as new plotting inputs, replacing the previous focus on only the older CDMS dataset examples.

### Impact
- The notebook now includes more recent experimental data.
- It is better suited to showing modern direct-detection exclusion/constraint curves.

## 4. Figure styling was refined

Before:

```python
fig = plt.figure(figsize=(10, 10), linewidth=0, edgecolor='#D0D6DB', facecolor='#D0D6DB')
ax.tick_params(axis='both', labelsize=16)
```

After:

```python
fig = plt.figure(figsize=(10, 7), linewidth=0, edgecolor='#FFFFFF', facecolor='#FFFFFF')
ax.tick_params(axis='both', which='major', direction='in', top=True, right=True, length=9, width=1.5, labelsize=16)
ax.tick_params(axis='both', which='minor', direction='in', top=True, right=True, length=5, width=1.1)
```

### Impact
- Cleaner, lighter visual style.
- More precise tick control with inward direction and thicker major/minor ticks.

## 5. Plot data source changed

Before:

```python
data = get_current_plots_data()
```

After:

```python
data = get_current_plots_data(LZ_2025)
```

### Impact
- The plotting backend now explicitly uses the new LZ dataset instead of the earlier CDMS-based example.

## 6. Axis labeling and scientific formatting were updated

Before:

```python
ax.set_ylabel(r"$\mathrm{Cross\ Section}\ [cm^{2}]\ (\mathrm{normalized\ to\ nucleon})$", fontsize=18)
ax.set_xlabel(get_x_label(selected_unit), fontsize=18)
ax.set_title(plot_title, fontsize=18)
```

After:

```python
ax.set_ylabel(r"$\mathrm{DM-nucleon}\ \sigma_{\mathrm{SI}} \ [\mathrm{cm}^{2}]$", fontsize=18, labelpad=5)
ax.set_xlabel(r"$\mathrm{DM \ Mass}\  [\mathrm{GeV/c^2}]$", fontsize=18, labelpad=5)
#ax.set_title(plot_title, fontsize=18, pad=5)
```

### Impact
- The labels are more specific to dark-matter SI cross-section terminology.
- The title was commented out, simplifying the final rendered plot.

## 7. Log-scale tick configuration was added

New code:

```python
ax.xaxis.set_major_locator(LogLocator(base=10))
ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1))
ax.xaxis.set_major_formatter(LogFormatterMathtext())

ax.yaxis.set_major_locator(LogLocator(base=10))
ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1))
ax.yaxis.set_major_formatter(LogFormatterMathtext())
```

### Impact
- Logarithmic axes render more cleanly and consistently.
- Minor tick spacing is more precise for scientific plotting.

## 8. Typography and spine styling were improved

New code:

```python
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "cm"
})

for spine in ax.spines.values():
    spine.set_linewidth(1.4)
```

### Impact
- More polished, publication-style appearance.
- Better consistency with typical scientific plots.

## 9. New imports added for log tick handling

Added imports:

```python
from matplotlib.ticker import LogLocator, LogFormatterMathtext
from matplotlib.ticker import MultipleLocator
```

### Impact
- Enables the improved log-axis tick controls seen in the updated plot rendering.

## Summary

The newer notebook is a significant update to the plotting pipeline:

- It switches to a more general dataset-driven plotting helper.
- It adds modern LZ direct-detection data.
- It upgrades the aesthetics and scientific labeling of the plot.
- It improves log-axis formatting and final layout for better publication-style output.

