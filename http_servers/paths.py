import os

def relative_to_absolute_path(relative_path, relative_dir=None):
    """
    Convert a relative path to an absolute path.  All relative paths are
    relative to the workspace directory unless otherwise specified.
    """
    if relative_dir is not None:
        # Combine the relative directory with the relative path
        return os.path.join(relative_dir, relative_path)
    else:
        # Get the directory of this file, and set the workspace directory to
        # the parent directory of this file's directory
        relative_dir = os.path.dirname(os.path.dirname(__file__))
        # Combine the directory of this file with the relative path
        return os.path.join(relative_dir, relative_path)
