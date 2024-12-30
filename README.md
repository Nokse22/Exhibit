<img height="128" src="data/icons/hicolor/scalable/apps/io.github.nokse22.Exhibit.svg" align="left"/>

# Exhibit
  [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
  [![made-with-python](https://img.shields.io/badge/Made%20with-Python-ff7b3f.svg)](https://www.python.org/)
  [![Downloads](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=Flathub%20Downloads&query=%24.installs_total&url=https%3A%2F%2Fflathub.org%2Fapi%2Fv2%2Fstats%2Fio.github.nokse22.Exhibit)](https://flathub.org/apps/details/io.github.nokse22.Exhibit)
  

View 3D models, powered by the [F3D](https://github.com/f3d-app/f3d) library that supports many file formats, from digital content to scientific datasets (including glTF, USD, STL, STEP, PLY, OBJ, FBX, Alembic)

<div align="center">
    <img src="data/resources/screenshot 1.png" max-height="500"/>
</div>
<details>
<summary>Click for more screenshots</summary>
    <div align="center">
    <img src="data/resources/screenshot 2.png" max-height="500"/>
    <img src="data/resources/screenshot 3.png" max-height="500"/>
    <img src="data/resources/screenshot 4.png" max-height="500"/>
    <img src="data/resources/screenshot 5.png" max-height="500"/>
    <img src="data/resources/screenshot 6.png" max-height="500"/>
    <img src="data/resources/screenshot 7.png" max-height="500"/>
    </div>
</details>

### Screenshots Credits
- [Planetary reducer](https://sketchfab.com/3d-models/planet-reducer-animation-273823b0b7014a31a1ef2e1148ca8205)
- [Retro computer setup](https://sketchfab.com/3d-models/retro-computer-setup-free-82eaf2047e0447a1bfea22482f1d1404)
- [Benchy](https://www.printables.com/model/3161-3d-benchy#preview:file-3QVl)
- [Nissan Fairlady](https://sketchfab.com/3d-models/nissan-fairlady-z-s30240z-1978-0d9286ebb8cc426e993e1d398b874a34)
- [Vase](https://sketchfab.com/3d-models/vase-rawscan-98a29620a45e47ccb80a75d5416c8255)
- [Point Cloud Ship](https://sketchfab.com/3d-models/mv-spartan-point-cloud-3bf41cd55bd1406b99f7008c0184a057)

## Installation

### Flathub
<a href='https://flathub.org/apps/io.github.nokse22.Exhibit'>
<img height='80' alt='Get it on Flathub on Flathub' src='https://flathub.org/api/badge'/>
</a>

### From latest build

Go to the [Actions page](https://github.com/Nokse22/Exhibit/actions), click on the latest working build and download the Artifact.
Extract the downloaded .zip file and install it clicking on the flatpak file or with:

`flatpak install io.github.nokse22.Exhibit.flatpak`

### From source

You just need to clone the repository

```sh
git clone https://github.com/Nokse22/Exhibit.git
```

Open the project in GNOME Builder and click "Run Project".

## Help

You can view the extended help pages from `Main Menu > Help` or by pressing `F1`.

### Custom Configurations
Custom configurations are saved in `/home/username/.var/app/io.github.nokse22.Exhibit/data/configurations`. The best way to make a custom configuration is to use the app and save it to file, but if you want to use some of the supported options that don't have an UI you will need to later edit it manually.

The default configurations can not be changed, but if one of your custom configurations supports the file you are opening it will have priority over the default ones.

### HDRI
There are 4 default 1k HDRIs, you can add more by opening the HDRIs folder from the app hamburger menu and placing them there. Any image added in this path will be used as an HDRI and a thumbnail will be generated. Images added when the app is running will be visible the next time the app is started.

If you save a configuration that uses an HDRI make sure it is placed in this folder, this way the app will always be able to access the file.

### Options
To view all the options description and also all the supported options that don't have an UI you can visit the `Options` page in the `Help`.

## License

Exhibit is distributed under the GPLv3 license, it uses F3D that is distributed under the 3-Clause BSD License, see [this](https://github.com/f3d-app/f3d?tab=readme-ov-file#license) for more info on F3D libraries licenses.
