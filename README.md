# Installation

Dreamcenter uses conda for environment management.
This ensures that the right version of python and pygame (as well as other dependencies) are installed.

Install miniconda first.

Next, set up the dedicated conda environment for dreamcenter:

`conda env create -f conda.yaml`

Next, activate the conda environment:

`conda activate dreamcenter`

# Running game

(From the project root directory)
`python -m dreamcenter.main launch`

Map Editor.
press 2 to start placing tiles.
scroll wheel to change tile.
F5 to save design.

Gameplay.
mouse to shoot.
wasd to move.
