#!/bin/bash
# Shell script to re-configure the python virtual environment (venv) in which Tartube runs, in case
#       the automatic re-configuration fails
# Does not attempt to repair Tartube itself, does not modify the saved data file, settings.json, and
#       does not open Tartube when it the re-configutation is finished
#
# N.B. This script is almost identical to tartube_mswin.sh, except (1) Tartube is not actually
#       started, and (2) success/failure messages are written to the terminal
#
# This script should be run from the Tartube source code folder, i.e. the one that contains the
#       setup.py file:
#
# 1. Open the mingw64 terminal. In Tartube, click:
#       System > Open MSYS2 terminal
# 2. Type these commands:
#       cd tartube
#       ./tartube_repair.sh

echo "tartube_mswin.sh: Starting re-configuration of Python's virtual environment (venv)..."

# Prepare system environment
export PATH="/mingw64/bin:/usr/local/bin:/usr/bin:/bin"
# Ensure working directory is /home/user, not /home/[current Windows account name] 
cd /home/user/tartube

# Get the directory for the python venv that was created for the Tartube installer
VENV_DIR="../ytdl-venv"

# The venv contains file paths that were correct, when the installer was created; we need to convert
#   them to the equivalent paths for the installation
# This means overwriting the files .../ytdl-venv/pyvenv.cfg and .../ytdl-venv/bin/activate

# Relative path to pyvenv.cfg file
cfg_file="$VENV_DIR/pyvenv.cfg"
# Other relative paths
bin_path="../../../mingw64/bin"
python_path="../../../mingw64/bin/python.exe"

if [[ -f "$cfg_file" ]] ; then 

	# Convert relative paths to MSWin paths 
	bin_path_mswin="$(cygpath -m "$bin_path")"
	python_path_mswin="$(cygpath -m "$python_path")"
	venv_dir_mswin="$(cygpath -m "$VENV_DIR")"
    		
	# Overwrite the contents of the file to set correct paths
	sed -i "/^home = /s|.*|home = $bin_path_mswin|" "$cfg_file"
	sed -i "/^executable = /s|.*|executable = $python_path_mswin|" "$cfg_file"
	sed -i "/^command = /s|.*|command = $python_path_mswin -m venv $venv_dir_mswin|" "$cfg_file"

	echo "tartube_mswin.sh: updated venv paths in $cfg_file"

else

	echo "tartube_mswin.sh: could not find file: $cfg_file"
    	
fi

# Relative path to activate file
act_file="$VENV_DIR/bin/activate"
if [[ -f "$act_file" ]] ; then 

	# Convert relative paths to MSWin paths 
	venv_dir_mswin="$(cygpath -m "$VENV_DIR")"

	# Overwrite the contents of the file to set correct paths
	sed -i "s|VIRTUAL_ENV=\$(cygpath [^)]*)|VIRTUAL_ENV=\$(cygpath $venv_dir_mswin)|" "$act_file"
	sed -i "s|export VIRTUAL_ENV=.*|EXPORT VIRTUAL_ENV=$venv_dir_mswin|" "$act_file"

	echo "tartube_mswin.sh: updated venv paths in $act_file"

else

	echo "tartube_mswin.sh: could not find file: $act_file"

fi

# Set the python venv for this instance of Tartube
export VIRTUAL_ENV="$VENV_DIR"
export PATH="$VENV_DIR/bin:$PATH"

# Optional instructions
#alias python3="$VENV_DIR/bin/python3.exe"
#alias pip="$VENV_DIR/bin/pip.exe"

# Activate the venv
#source /home/user/ytdl-venv/bin/activate 

# Start Tartube
#cd /home/user/tartube
#GTK_OVERLAY_SCROLLING=0 python3 -X utf8 tartube/tartube
