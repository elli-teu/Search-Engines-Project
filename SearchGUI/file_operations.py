import glob
from constants import *
import game_engine


def save_image(image, desired_image_path):
    """Saves an image.

    Args:
        image (bytes): An image in bytes format.
        desired_image_path (str): The file path where the image should be saved.
    """
    with open(desired_image_path, "wb") as image_file:
        image_file.write(image)


def load_image(image_path):
    """Loads the image with the given image_path.

    Args:
        image_path (str): The path of the image to be loaded.
    """
    return game_engine.get_surface_manager().load_image(image_path)


def image_exists(image_name):
    """Checks if an image exists or not in the image directory, based on the images' name.

    Args:
        image_name (str): The name of the image.

    Returns:
        bool: True if the image exists, False otherwise.
    """
    image_paths = []
    for image_type in allowed_image_types:
        image_paths.extend(glob.glob(image_location + image_name + image_type))

    return len(image_paths) != 0


def find_image_path_from_name(image_name):
    """Finds the first matching file for the given file name in the image location.

    Args:
        image_name (str): The name of the image.

    Returns:
        str: The full path of the image.
    """
    image_paths = []
    for image_type in allowed_image_types:
        image_paths.extend(glob.glob(image_location + image_name + image_type))

    return str(image_paths[0])


def load_all_images():
    """Loads all images in the '/Images/' directory, to improve performance."""
    image_paths = []
    for image_type in allowed_image_types:
        image_paths.extend(glob.glob(image_location + "*" + image_type))

    for image_path in image_paths:
        load_image(str(image_path))