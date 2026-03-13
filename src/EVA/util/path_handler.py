import sys
import os
from typing import AnyStr


def get_path(path: AnyStr) -> AnyStr:
    """
    Args:
        path: Path to file relative to content root

    Returns:
        Modified path

    Checks if program is running from executable form, if so, modify path to ensure path is valid.
    (Because the paths will not work as normal when running from executable)
    """
    # check if running from the executable or not
    bundle_dir = getattr(sys, "_MEIPASS", "")
    return os.path.abspath(os.path.join(bundle_dir, path))
