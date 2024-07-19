# Options

## View Options
### With UI
These options can be changed using the UI.
| Option | Type | Default Value | libf3d option | Description |
|-|-|-|-|-|
|grid|bool|True|render.grid.enable|View the grid|
|grid-absolute|bool|False|render.grid.absolute|Position the grid at the origin|
|translucency-support|bool|True|render.effect.translucency-support|Support translucent objects|
|tone-mapping|bool|False|render.effect.tone-mapping|Make the colors correct on your screen|
|ambient-occlusion|bool|False|render.effect.ambient-occlusion|This is a technique providing approximate shadows, used to improve the depth perception of the object. Implemented using SSAO|
|anti-aliasing|bool|True|render.effect.anti-aliasing|This technique is used to reduce aliasing, implemented using FXAA|
|hdri-ambient|bool|False|render.hdri.ambient|Illuminate the model using the loaded HDRI or the default one|
|hdri-skybox|bool|False|render.background.skybox|Use the loaded HDRI as a background|
|blur-background|bool|True|render.background.blur|Blurs the background|
|light-intensity|-|1.0|render.light.intensity|Intensity of all the lights in the scene|
|orthographic|bool|False|scene.camera.orthographic|Use an orthographic camera|
|blur-coc|-|20.0|render.background.blur.coc|Blur circle of confusion|
|background-color|-|(1.0, 1.0, 1.0)|render.background.color|Color of the background, will be viewed only if `use-color` is `True`|
|show-edges|-|False|render.show-edges|Show all the edges of the model, some models can define edges that will be viewed always|
|edges-width|-|1.0|render.line-width|Width of all the edges in a scene|
|up|string|"+Y"|scene.up-direction|Direction of the up|
|show-points|bool|False|model.point-sprites.enable|Show sphere points sprites instead of the geometry|
|point-size|-|1.0|render.point-size|Size of points when showing vertices and point sprites|
|model-color|-|(1.0, 1.0, 1.0)|model.color.rgb|Color on the geometry. Multiplied with the model.color.texture when present|
|model-metallic|-|0.0|model.material.metallic|Set the metallic coefficient on the geometry (0.0-1.0). Multiplied with the model.material.texture when present|
|model-roughness|-|0.3|model.material.roughness|Roughness coefficient on the geometry (0.0-1.0). Multiplied with the model.material.texture when present|
|model-opacity|-|1.0|model.color.opacity|Opacity on the geometry. Usually used with Depth Peeling option. Multiplied with the model.color.texture when present|
|comp|-|-1|model.scivis.component|Component to color with. -1 means magnitude. -2 means direct values.|
|hdri-file|string|""|render.hdri.file|Path to the HDRI file|
|cells|bool|True|model.scivis.cells|Color the data with value found on the cells instead of points|

### Without UI
These options are supported, but can only be changed making a configuration file by hand.
| Option | Type | Default Value | libf3d option | Description |
|-|-|-|-|-|
|texture-matcap|string|""|model.matcap.texture|-|-|
|texture-base-color|-|-|model.color.texture|-|-|
|emissive-factor|-|(1.0, 1.0, 1.0)|model.emissive.factor|-|-|
|texture-emissive|-|""|model.emissive.texture|-|-|
|texture-material|-|""|model.material.texture|-|-|
|normal-scale|-|1.0|model.normal.scale|-|-|
|texture-normal|-|""|model.normal.texture|-|-|
|point-sprites|bool|False|model.point-sprites.enable|-|-|
|point-type|string|"sphere"|model.point-sprites.type|-|-|
|volume|bool|False|model.volume.enable|-|-|
|inverse|bool|False|model.volume.inverse|-|-|
|final-shader|string|""|render.effect.final-shader|-|-|
|grid-unit|-|0.0|render.grid.unit|-|-|
|grid-subdivisions|-|10|render.grid.subdivisions|-|-|
|grid-color|-|(0.0, 0.0, 0.0)|render.grid.color|-|-|
|bg-color|-|(0.2, 0.2, 0.2)|render.background.color"

## Other Options
These options can be changed with the UI and saved in a configuration file.
| Option | Type | Default Value | Description |
|-|-|-|-|
|use-color|bool|False|Whether or not to use `bg-color` as a background|
|point-up|bool|True|Keeps the model always pointing up|
|auto-reload|bool|False|Check if the file has changed and reload|

## Making a custom configuration
The best way to make a configuration is to use the app and save it to file, but if you want to use settings without UI you will need to edit it manually.

This is an example configuration:
```
{
    "example": {
        "name": "Example",
        "formats": ".*(stl|3mf)",
        "view-settings": {
            "model-metallic": 0.7,
            "model-roughness": 0.3,
            "model-opacity": 1.0,
            "model-color": [
                0.9019607843137255,
                0.3803921568627451,
                0.0
            ]
        },
        "other-settings": {
            "use-color": false,
            "point-up": true,
            "auto-reload": false
        }
    }
}
```
You can add any option to the dictionary, make sure to put the view options in the `view-settings` dictionary and the others in the `other-settings`.
