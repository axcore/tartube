# Copyright © 2016-2019 Scott Stevenson <scott@stevenson.io>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#
# Tartube v2.0.0
# Imported into Tartube and renamed, so the Debian/RPM packagers don't confuse
#   it with the standard xdg module.

"""XDG Base Directory Specification variables.

XDG_CACHE_HOME, XDG_CONFIG_HOME, and XDG_DATA_HOME are pathlib.Path
objects containing the value of the environment variable of the same
name, or the default defined in the specification if the environment
variable is unset or empty.

XDG_CONFIG_DIRS and XDG_DATA_DIRS are lists of pathlib.Path objects
containing the value of the environment variable of the same name split
on colons, or the default defined in the specification if the
environment variable is unset or empty.

XDG_RUNTIME_DIR is a pathlib.Path object containing the value of the
environment variable of the same name, or None if the environment
variable is not set.

"""

import os
from pathlib import Path
from typing import List, Optional

__all__ = [
    "XDG_CACHE_HOME",
    "XDG_CONFIG_DIRS",
    "XDG_CONFIG_HOME",
    "XDG_DATA_DIRS",
    "XDG_DATA_HOME",
    "XDG_RUNTIME_DIR",
]

HOME = Path(os.path.expandvars("$HOME"))


def _path_from_env(variable: str, default: Path) -> Path:
    """Read an environment variable as a path.

    The environment variable with the specified name is read, and its
    value returned as a path. If the environment variable is not set, or
    set to the empty string, the default value is returned.

    Parameters
    ----------
    variable : str
        Name of the environment variable.
    default : Path
        Default value.

    Returns
    -------
    Path
        Value from environment or default.

    """
    # TODO(srstevenson): Use assignment expression in Python 3.8.
    value = os.environ.get(variable)
    if value:
        return Path(value)
    return default


def _paths_from_env(variable: str, default: List[Path]) -> List[Path]:
    """Read an environment variable as a list of paths.

    The environment variable with the specified name is read, and its
    value split on colons and returned as a list of paths. If the
    environment variable is not set, or set to the empty string, the
    default value is returned.

    Parameters
    ----------
    variable : str
        Name of the environment variable.
    default : List[Path]
        Default value.

    Returns
    -------
    List[Path]
        Value from environment or default.

    """
    # TODO(srstevenson): Use assignment expression in Python 3.8.
    value = os.environ.get(variable)
    if value:
        return [Path(path) for path in value.split(":")]
    return default


XDG_CACHE_HOME = _path_from_env("XDG_CACHE_HOME", HOME / ".cache")

XDG_CONFIG_DIRS = _paths_from_env("XDG_CONFIG_DIRS", [Path("/etc/xdg")])

XDG_CONFIG_HOME = _path_from_env("XDG_CONFIG_HOME", HOME / ".config")

XDG_DATA_DIRS = _paths_from_env(
    "XDG_DATA_DIRS",
    [Path(path) for path in "/usr/local/share/:/usr/share/".split(":")],
)

XDG_DATA_HOME = _path_from_env("XDG_DATA_HOME", HOME / ".local" / "share")

try:
    XDG_RUNTIME_DIR: Optional[Path] = Path(os.environ["XDG_RUNTIME_DIR"])
except KeyError:
    XDG_RUNTIME_DIR = None
