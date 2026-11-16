# Color and style design for academic plotting

This note summarizes the design discussion for the plotting color and style workflow.

## Summary

The current proposal to allow a broad, global color parser is too permissive for a user-facing interface. It mixes several concerns into one value: color choice, opacity, fallback behavior, and validation. That makes the API harder to reason about and can silently hide invalid user input.

The recommended approach is:

- Keep color as a distinct, validated field.
- Keep opacity as a separate property, not encoded into the color string.
- Keep style as a rendering preset, not a free-form mix of unrelated visual properties.

## Recommended model

### 1. Color

Use a curated academic palette for the dropdown, especially for line plots and area fills. A strong default is the Okabe–Ito palette:

- black: `#000000`
- orange: `#E69F00`
- sky blue: `#56B4E9`
- bluish green: `#009E73`
- blue: `#0072B2`
- vermillion: `#D55E00`
- reddish purple: `#CC79A7`
- yellow: `#F0E442`

This palette is widely used in scientific visualization and is reasonably color-vision-deficiency friendly.

For the API, allow a broader Matplotlib-compatible color set if needed, but validate centrally using Matplotlib utilities rather than custom regex parsing.

### 2. Style

Treat style as a preset, not as a free-form set of unrelated properties. Example presets:

- solid line
- dashed line
- marker + solid line
- marker + dashed line
- fill light
- fill medium

Internally, these presets should map to specific values such as:

- `lineStyle`
- `marker`
- `lineWidth`
- `fillOpacity`

This avoids overloading a single field with multiple meanings.

### 3. Opacity

Opacity should not be embedded in the color value. For example, avoid inputs like `#3f0825.2` or any string that mixes a hex color and alpha. Instead, use:

- `color: "#3f0825"`
- `opacity: 0.2`

This keeps the color valid and predictable while keeping fill transparency explicit and easy to control.

## Why this is preferable

- Clear separation of concerns
- Easier validation and error handling
- More consistent behavior between dropdown and API
- Better user experience for scientific plotting
- Easier long-term maintenance

## Recommended API shape

A good conceptual API is:

```python
{
  "color": "#56B4E9",
  "opacity": 0.25,
  "lineStyle": "solid",
  "marker": None,
  "fillType": "light"
}
```

or, if using presets:

```python
{
  "color": "#0072B2",
  "stylePreset": "fill-medium"
}
```

with the preset internally resolving to the correct opacity and rendering settings.

## Final recommendation

The design should be:

- Color = hue selection
- Style preset = rendering configuration
- Opacity = separate numeric property
- Validated with Matplotlib-supported colors, not custom regex rules

This keeps the UI simple, the API robust, and the resulting charts academically appropriate without introducing brittle parsing logic.
