from constants import *

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


class SurfaceType:
    SURFACE = "surface"
    IMAGE = "image"
    FONT = "font"


class SurfaceHelper:
    """A helper class for managing surfaces in the game engine.

    Attributes:
        surface (pygame.Surface): The surface associated with this helper.
        surface_id (int): The unique identifier for the surface.
        size (tuple): The size of the surface (width, height).
        alpha (int): The alpha value of the surface.
        image_string (str): The string representation of the image (only for image surfaces).
        font_data (tuple): Tuple related to font surfaces (text, text_color, font_size).
        surface_type (str): The type of the surface (e.g SurfaceType.IMAGE).
    """

    def __init__(self, surface, surface_id, size=(0, 0), alpha=255, image_string="",
                 font_data=("", BLACK, 30),
                 surface_type=SurfaceType.SURFACE):
        """Initializes a SurfaceHelper instance.

        Args:
            surface(Pygame.surface): The surface associated with this helper.
            surface_id (int): The unique identifier for the surface.
            size (tuple):  The size of the surface (width, height).
            alpha (int): The alpha value of the surface.
            image_string (str): The string representation of the image (only for image surfaces).
            font_data (tuple): Tuple related to font surfaces (text, text_color, font_size).
            surface_type (str): The type of the surface (e.g., SurfaceType.IMAGE).
        """
        self.surface = surface.convert_alpha()
        self.surface_id = surface_id
        self.size = size[0], size[1]
        self.alpha = alpha
        self.image_string = image_string
        self.font_data = font_data
        self.surface_type = surface_type

    def get_surface(self):
        """Gets the surface associated with this object.

        Returns:
            pygame.Surface: The surface object.
        """
        if self.surface is not None:
            return self.surface

    def get_surface_id(self):
        """Gets the unique identifier of the surface.

        Returns:
            int: The unique identifier of the surface.
        """
        return self.surface_id

    def get_size(self):
        """Gets the size of the surface.

        Returns:
            tuple: The size of the surface as a tuple (width, height).
        """
        return self.size

    def get_alpha(self):
        """Gets the alpha value of the surface.

        Returns:
            int: The alpha value of the surface.
        """
        return self.alpha

    def get_image_string(self):
        """Gets the string representation of the surface's image data.

        Returns:
            str: The image data as a string.
        """
        return self.image_string

    def get_font_data(self):
        """Gets the font data tuple (text, color, size).

        Returns:
            tuple: The tuple representing the font data.
        """
        return self.font_data

    def get_surface_type(self):
        """Gets the type of the surface (e.g., SurfaceType.SURFACE).

        Returns:
            str: The type of the surface.
        """
        return self.surface_type

    def set_surface(self, surface):
        """Sets the surface of the SurfaceHelper instance.

        Args:
            surface (Pygame.Surface): The new surface.
        """
        self.surface = surface

    def set_size(self, size):
        """Sets the size of the surface.

        Args:
            size (tuple): The new size of the surface as a tuple (width, height).
        """
        self.size = size

    def prepare_for_saving(self):
        """Prepares the surface for saving by setting it to None."""
        self.surface = None

    def copy(self):
        """Creates a copy of the SurfaceHelper instance.

       Returns:
           SurfaceHelper: A new SurfaceHelper instance with the same attributes.
       """
        new_surface_helper = SurfaceHelper(self.get_surface(), self.get_surface_id(), self.get_size(),
                                           self.get_alpha(), self.get_image_string(), self.get_font_data(),
                                           self.get_surface_type())

        return new_surface_helper


class SurfaceManager:
    """A class used for handling surfaces.

    Attributes:
        current_max_id (int): The current maximum surface identifier.
        fonts (dict): Dictionary to store Pygame font objects.
        image_path_id_dict (dict): Dictionary mapping image paths to surface IDs.
        surface_objects (dict): Dictionary to store SurfaceHelper objects.
    """

    # TODO: Need some way to remove surfaces that are no longer used.
    def __init__(self):
        """Initializes a SurfaceManager instance."""
        self.current_max_id = 0
        self.fonts = {}
        self.image_path_id_dict = {}
        self.surface_objects = {}

    def get_new_id(self):
        """Generates a new unique surface identifier.

        Returns:
            int: The new surface identifier.
        """
        new_id = self.current_max_id + 1
        self.current_max_id += 1
        return new_id

    def add_surface(self, surface, surface_id=None, alpha=255, image_string="",
                    font_data=("", BLACK, 30),
                    surface_type=SurfaceType.SURFACE):
        """Adds a new surface to the manager and returns its identifier.

        Args:
            surface (Pygame.surface): The surface object.
            surface_id (int or None): The unique identifier for the surface.
            alpha (int): The alpha value of the surface (transparency).
            image_string (str): String representation of the surface's image data.
            font_data (tuple): Tuple containing font information (text, color, size).
            surface_type (str): The type of the surface (e.g., SurfaceType.SURFACE).

        Returns:
            int: The identifier of the added surface.
        """
        if surface_id is None:
            surface_id = self.get_new_id()
        surface_object = SurfaceHelper(surface, surface_id, size=surface.get_size(), alpha=alpha,
                                       image_string=image_string,
                                       font_data=font_data, surface_type=surface_type)
        self.surface_objects[surface_object.get_surface_id()] = surface_object
        return surface_object.get_surface_id()

    def remove_surface(self, surface_id):
        """Removes the surface associated with the provided surface id.

        Args:
            surface_id (int): The id of the surface.
        """
        del self.surface_objects[surface_id]

    def fetch_surface(self, surface_id):
        """Returns the Pygame surface object associated with the given surface identifier.

        Args:
            surface_id (int): The unique identifier of the surface.

        Returns:
            pygame.Surface: The surface object.
        """
        return self.surface_objects[surface_id].get_surface()

    def create_surface(self, width, height, alpha=255, surface_id=None):
        """Creates a new surface.

        Args:
            width (int): The width of the new surface.
            height (int): The height of the new surface.
            alpha (int): The alpha value of the new surface (transparency).
            surface_id (int or None): The unique identifier for the new surface.

        Returns:
            int: The identifier of the newly created surface.
        """
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.set_alpha(alpha)
        surface_id = self.add_surface(surface, surface_id=surface_id, alpha=alpha)
        return surface_id

    def create_temporary_surface(self, width, height, alpha=255):
        """Creates a new temporary surface.

        Args:
            width (int): The width of the new surface.
            height (int): The height of the new surface.
            alpha (int): The alpha value of the new surface (transparency).

        Returns:
            int: The identifier of the newly created surface.
        """
        return self.create_surface(width, height, alpha, -1)

    def restore_surface(self, surface_id):
        """Restores the surface with the given surface id.

        Args:
            surface_id (int): The unique identifier of the surface to be restored.
        """
        surface_object = self.surface_objects[surface_id]
        width, height = surface_object.get_size()
        self.create_surface(width, height, surface_object.get_alpha(), surface_id)

    def transform_surface(self, surface_id, size, rotation_angle, new_id=None):
        """Transforms a surface by scaling and rotating it.

        Args:
            surface_id (int): The unique identifier of the surface to be transformed.
            size (tuple): The new size of the surface as a tuple (width, height).
            rotation_angle (int): The rotation angle in degrees.
            new_id (int): The unique identifier for the new transformed surface. If None, a new ID is created.

        Returns:
            int: The new identifier of the transformed surface.
        """
        surface = self.fetch_surface(surface_id)
        rotated_and_scaled_surface = self._transform_surface(surface, size, rotation_angle)
        new_id = self.add_surface(rotated_and_scaled_surface, alpha=surface.get_alpha(), surface_id=new_id)
        return new_id

    @staticmethod
    def _transform_surface(surface, size, rotation_angle):
        """Applies scaling and rotation to a surface.

       Args:
           surface (pygame.Surface): The surface to be transformed.
           size (tuple): The new size of the surface as a tuple (width, height).
           rotation_angle (int): The rotation angle in degrees.

       Returns:
           pygame.Surface: The transformed surface.
       """
        if rotation_angle != 0:
            rotated_surface = pygame.transform.rotate(surface, rotation_angle)
        else:
            rotated_surface = surface

        if size != rotated_surface.get_size():
            rotated_and_scaled_surface = pygame.transform.smoothscale(rotated_surface, size)
        else:
            rotated_and_scaled_surface = rotated_surface

        return rotated_and_scaled_surface

    def reset_surface(self, surface_id):
        self.fetch_surface(surface_id).fill((0, 0, 0, 0))
        return surface_id

    def load_image(self, image_path):
        """Loads the image with the specified image path and returns its identifier.

        Args:
            image_path (str): The image path of the image to be loaded.

        Returns:
            int: The identifier of the loaded image.
        """
        if image_path in self.image_path_id_dict:
            return self.image_path_id_dict[image_path]

        image = pygame.image.load(image_path)
        image.set_alpha(255)
        image_id = self.set_image(image)
        self.image_path_id_dict[image_path] = image_id
        return image_id

    def set_image(self, image, image_id=None):
        """Sets an image as a surface and returns its identifier.

        Args:
            image (pygame.Surface): The surface representing the image.
            image_id (int or None): The unique identifier for the image.

        Returns:
            int: The identifier of the set image.
        """
        image_string = pygame.image.tostring(image, 'RGBA')
        image_id = self.add_surface(image, alpha=image.get_alpha(), surface_id=image_id,
                                    image_string=image_string,
                                    surface_type=SurfaceType.IMAGE)
        return image_id

    def fetch_image(self, image_id):
        """Returns the image surface associated with the given image identifier.

        Args:
            image_id (int): The unique identifier of the image.

        Returns:
            pygame.Surface: The image surface.
        """
        return self.fetch_surface(image_id)

    def transform_image(self, image_id, size, rotation_angle, new_id=None):
        """Transforms an image by scaling and rotating it.

        Args:
            image_id (int): The unique identifier of the image to be transformed.
            size (tuple): The new size of the image as a tuple (width, height).
            rotation_angle (int): The rotation angle in degrees.
            new_id (int or None): The unique identifier for the new transformed image. If None, a new ID is created.

        Returns:
            int: The identifier of the transformed image.
        """
        image = self.fetch_image(image_id)
        scaled_and_rotated_image = self._transform_surface(image, size, rotation_angle)
        new_id = self.set_image(scaled_and_rotated_image, image_id=new_id)
        return new_id

    def restore_image(self, image_id):
        """Restores the image with the specified image identifier.

        Args:
            image_id (int): The unique identifier of the image to be restored.
        """
        surface_object = self.surface_objects[image_id]
        image_string = surface_object.get_image_string()
        size = surface_object.get_size()
        restored_image = pygame.image.fromstring(image_string, size, "RGBA")
        surface_object.set_surface(restored_image)

    def create_font(self, size):
        """Creates a font object with the specified size, with the font 'Arial'.

        Args:
            size (int): The size of the font.

        Returns:
            pygame.font.Font: The font object.
        """
        font = pygame.font.SysFont("Arial", size)
        self.fonts[size] = font
        return font

    def get_font(self, size):
        """Gets the font object for the specified size, creating one if no such font exists.

        Args:
            size (int): The size of the font.

        Returns:
            pygame.font.Font: The font object.
        """
        if size in self.fonts:
            font = self.fonts[size]
        else:
            font = self.create_font(size)

        return font

    def create_font_surface(self, text, text_color, font_size, font_surface_id=None):
        """Creates a font surface and returns its identifier.

        Args:
            text (str): The text to be rendered.
            text_color (tuple): The color of the text as a tuple (R, G, B).
            font_size (int): The size of the font.
            font_surface_id (int or None): The unique identifier for the font surface.

        Returns:
            int: The identifier of the font surface.
        """
        font = self.get_font(font_size)
        font_surface = font.render(text, True, text_color)
        font_data = (text, text_color, font_size)
        font_surface_id = self.add_surface(font_surface, surface_id=font_surface_id, alpha=255, font_data=font_data,
                                           surface_type=SurfaceType.FONT)
        return font_surface_id

    def create_temporary_font_surface(self, text, text_color, font_size):
        """Creates a font surface and returns its identifier.

        Args:
            text (str): The text to be rendered.
            text_color (tuple): The color of the text as a tuple (R, G, B).
            font_size (int): The size of the font.

        Returns:
            int: The identifier of the font surface.
        """
        return self.create_font_surface(text, text_color, font_size, -1)

    def fetch_font_surface(self, font_surface_id):
        """Returns the Pygame font surface associated with the given identifier.

        Args:
            font_surface_id (int): The unique identifier of the font surface.

        Returns:
            pygame.Surface: The font surface.
        """
        return self.surface_objects[font_surface_id].get_surface()

    def restore_font_surface(self, surface_id):
        """Restores the font surface with the specified identifier.

        Args:
            surface_id (int): The unique identifier of the font surface to be restored.
        """
        surface_object = self.surface_objects[surface_id]
        text, color, font_size = surface_object.get_font_data()
        self.create_font_surface(text, color, font_size, surface_id)

    def load_surfaces(self, loaded_game_state):
        """Loads surfaces from a game state object.

        Args:
            loaded_game_state: The loaded game state object.
        """
        self.current_max_id = loaded_game_state.current_max_id
        self.surface_objects = loaded_game_state.surface_objects
        self.image_path_id_dict = loaded_game_state.image_path_id_dict
        self.fonts = {}
        for surface_id, surface_object in self.surface_objects.items():
            surface_type = surface_object.get_surface_type()
            if surface_type == SurfaceType.SURFACE:
                self.restore_surface(surface_id)
            elif surface_type == SurfaceType.IMAGE:
                self.restore_image(surface_id)
            elif surface_type == SurfaceType.FONT:
                self.restore_font_surface(surface_id)

    def copy(self):
        """Creates a copy of the SurfaceManager instance.

        Returns:
            SurfaceManager: A new SurfaceManager instance with the same attributes.
        """
        new_surface_manager = SurfaceManager()
        new_surface_manager.current_max_id = self.current_max_id
        new_surface_manager.surface_objects = {surface_id: surface_object.copy() for surface_id, surface_object in
                                               self.surface_objects.items()}
        for surface_id, surface_object in self.surface_objects.items():
            new_surface_manager.surface_objects[surface_id] = surface_object.copy()
        new_surface_manager.image_path_id_dict = self.image_path_id_dict.copy()
        new_surface_manager.fonts = {}
        return new_surface_manager
