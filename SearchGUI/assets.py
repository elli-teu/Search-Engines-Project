from constants import *
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from game_engine import environment
import game_engine
import utility_functions as utils
import time
import file_operations as file_op


# TODO: Change external_process_function functionality into a GameScript object instead.
# TODO: Split GameObject into two classes, one that is required for use when the object is displayed, and has
# necessary attributes like destroyed, children, etc, and one class that has position, width, rect, etc.


class GameScript:
    """Represents a game script."""

    def __init__(self):
        pass

    def process(self):
        pass


class CenteringOptions:
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class GameObject:
    """A Class for representing a GameObject.

    Attributes:
        x (int): X-coordinate of the object, rounded to the nearest integer.
        y (int): Y-coordinate of the object, rounded to the nearest integer.
        z (float): Z-coordinate of the object.
        width (int): Width of the object, rounded to the nearest integer.
        height (int): Height of the object, rounded to the nearest integer.
        alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
        name (str): Name of the object.
        destroyed (bool): Indicates whether the object has been destroyed.
        parent: Parent object to which this object is attached.
        static (bool): Indicates whether the object is static (does not move together with its parent).
        displayable (bool): Indicates whether the object is visible.
        opaque (bool): Indicates whether the object blocks objects earlier in the processing order from
            being clicked.
        opaque_to_ancestor (bool): Indicates whether the object should block clicks for objects that are its ancestor
            (is closer to the shared root parent than the other object) if they share the same z-value.
        opaque_to_descendant (bool): Indicates whether the object should block clicks for objects that are its
            descendant (is further from the shared root parent than the other object) if they share the same z-value.
        opaque_to_sibling (bool): Indicates whether the object should block clicks for objects that are its
            siblings (is the same distance from the shared root parent as the other object) if they share the same
            z-value.
        children (list): List of child objects.
        rect (pygame.Rect): Rectangular area occupied by the object.
        rotation_angle (int): Rotation angle of the object in degrees.
        relative_x (int): The x-coordinate of the object in relation to its parent, if applicable.
        relative_y (int): The y-coordinate of the object in relation to its parent, if applicable.
        x_centering (str): Indicates how the x-coordinate of the object should be centered when it is resized etc.
        y_centering (str): Indicates how the y-coordinate of the object should be centered when it is resized etc.
   """

    def __init__(self, x=0, y=0, z=0, width=0, height=0, alpha=255, parent=None, static=True, opaque=True,
                 opaque_to_ancestor=True, opaque_to_descendant=False, opaque_to_sibling=False,
                 x_centering=CenteringOptions.LEFT, y_centering=CenteringOptions.TOP,
                 displayable=False, name=""):
        """Initializes a GameObject.

        Args:
            x (float): The x-coordinate of the object.
            y (float): The y-coordinate of the object.
            z (float): The z-coordinate of the object.
            width (float): The width of the object.
            height (float): The height of the object.
            alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
            name (str): The name of the object.
            parent: The parent object to which this object is attached.
            static (bool): Indicates whether the object is static (does not move together with its parent).
            displayable (bool): Indicates whether the object is visible.
            x_centering (str): Indicates how the x-coordinate of the object should be centered when it is resized etc.
            y_centering (str): Indicates how the y-coordinate of the object should be centered when it is resized etc.
            opaque (bool): Indicates whether the object blocks objects below it from being clicked.
            opaque_to_ancestor (bool): Indicates whether the object should block clicks for its ancestors, if they
                share the same z-value.
            opaque_to_descendant (bool):Indicates whether the object should block clicks for its descendants, if they
                share the same z-value.
            opaque_to_ancestor (bool): Indicates whether the object should block clicks for its siblings, if they
                share the same z-value.
        """
        self.x = round(x)
        self.y = round(y)
        self.z = z
        if width < 0:
            width = 0
        self.width = round(width)
        if height < 0:
            height = 0
        self.height = round(height)
        self.name = name
        self.destroyed = False
        self.parent = parent
        self.static = static
        self.displayable = displayable
        self.children = []
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.rotation_angle = 0
        self.alpha = alpha
        self.opaque = opaque
        self.opaque_to_ancestor = opaque_to_ancestor
        self.opaque_to_descendant = opaque_to_descendant
        self.opaque_to_sibling = opaque_to_sibling
        if self.parent is None:
            self.relative_x, self.relative_y = 0, 0
        else:
            self.relative_x, self.relative_y = self.x - self.parent.x, self.y - self.parent.y

        self.x_centering = x_centering
        self.y_centering = y_centering

    def get_rect(self):
        """Get rect of the object

        Returns:
            - Pygame.rect: The value of the object's rect attribute
        """
        return self.rect

    def set_x(self, x):
        """Sets the x-coordinate of the object and updates its position relative to its parent (if applicable), as well
        as updates the position of its children.

        Args:
            x (float): The new x-coordinate of the object.
        """
        self.x = round(x)
        self.propagate_new_position()

    def set_y(self, y):
        """Sets the x-coordinate of the game object and updates its position relative to its parent (if applicable),
        as well as updates the position of its children.

        Args:
            y (float): The new y-coordinate of the object.
        """
        self.y = round(y)
        self.propagate_new_position()

    def propagate_new_position(self):
        """Updates the position of the game objects related attributes, as well as its children's positions,
        after either the objects x or y coordinate has changed."""
        self.get_rect().update(self.x, self.y, self.width, self.height)
        self.update_relative_position()
        for child in self.children:
            if hasattr(child, "update_position_relative_to_parent"):
                child.update_position_relative_to_parent()

    def set_z(self, z):
        """Sets the z-coordinate of the game object and shifts the z-coordinate of its children by the change in the
        z-coordinate.

        Args:
            z (float): The new z-coordinate of the object
        """
        delta_z = self.z - z
        self.z = z
        for child in self.children:
            child.shift_z(delta_z)

    def set_pos(self, x, y):
        """Sets the x and y coordinates of the game object.

        Args:
            x (float): The new x-coordinate.
            y (float): The new y-coordinate.
        """
        self.set_x(x)
        self.set_y(y)

    def shift_x(self, delta_x):
        """Shift the game object's x-coordinate by a given amount.

        Args:
            delta_x (float): The change in the x-coordinate of the object.
        """
        self.set_x(self.x + delta_x)

    def shift_y(self, delta_y):
        """Shift the game object's x-coordinate by a given amount.

        Args:
            delta_y (float): The change in the y-coordinate of the object.
        """
        self.set_y(self.y + delta_y)

    def shift_z(self, delta_z):
        """Shifts the game object's z-coordinate by a given amount.

        Args:
            delta_z (float): The change in the z-coordinate of the object.
        """
        self.set_z(self.z + delta_z)

    def shift_pos(self, delta_x, delta_y):
        """Shift the game object's position by a given amount in both x and y directions.

        Args:
            delta_x (float): The amount to shift the x-coordinate.
            delta_y (float): The amount to shift the y-coordinate.
        """
        self.shift_x(delta_x)
        self.shift_y(delta_y)

    def set_relative_x(self, x):
        """Sets the relative x-coordinate of the game object relative to its parent.

         Args:
             x (float): The relative x-coordinate.
         """
        self.relative_x = x

    def set_relative_y(self, y):
        """Sets the relative y-coordinate of the game object relative to its parent.

         Args:
             y (float): The relative x-coordinate.
         """
        self.relative_y = y

    def set_pos_relative_to_parent(self, x, y):
        """Sets the relative position of the game object in relation to the parent.

        The coordinates (x, y) refer to the position in the parent's coordinate system.

        Args:
            x (float): The relative x-coordinate.
            y (float): The relative y-coordinate.
        """
        if self.static:
            return

        self.set_relative_x(x)
        self.set_relative_y(y)
        self.update_position_relative_to_parent()

    def update_relative_position(self):
        """Updates the relative position attributes of the game object relative to its parent."""
        if self.static or self.parent is None:
            return
        self.set_relative_x(self.x - self.parent.x)
        self.set_relative_y(self.y - self.parent.y)

    def update_position_relative_to_parent(self):
        """Updates the position of the game object relative to its parent."""
        if self.static or self.parent is None:
            return

        self.set_pos(x=self.parent.x + self.relative_x, y=self.parent.y + self.relative_y)

    def set_width(self, width):
        """Sets the width of the game object.

        Args:
            width (float): The new width.
        """
        if width < 0:
            return
        self.width = round(width)
        self.get_rect().update(self.x, self.y, self.width, self.height)

    def set_height(self, height):
        """Sets the height of the game object.

        Args:
            height (float): The new width.
        """
        if height < 0:
            return
        self.height = round(height)
        self.get_rect().update(self.x, self.y, self.width, self.height)

    def set_size(self, width, height):
        """Sets the width and height of the game object.

        Args:
            width (float): The new height.
            height (float): The new width.
        """
        self.set_width(width)
        self.set_height(height)

    def adjust_width(self, delta_w):
        """Change the width of the game object by a given amount.

        Args:
            delta_w (int): The change to the width.
        """
        self.set_width(self.width + delta_w)

    def adjust_height(self, delta_h):
        """Change the height of the game object by a given amount.

        Args:
            delta_h (int): The change to the height.
        """
        self.set_height(self.height + delta_h)

    def get_rotation(self):
        """Gets the rotation angle of the game object.

        Returns:
            int: The rotation angle in degrees.
        """
        return self.rotation_angle

    def set_rotation(self, angle):
        """Sets the rotation angle of the game object, and changes the size of the game object if necessary.

        Args:
            angle (int): The new rotation angle in degrees.
        """
        if ((self.rotation_angle - angle) // 90) % 2 == 1:
            self.set_size(self.height, self.width)

        if self.x_centering == CenteringOptions.CENTER:
            self.shift_x(self.height / 2 - self.width / 2)

        if self.x_centering == CenteringOptions.RIGHT:
            self.shift_x(self.height - self.width)

        if self.y_centering == CenteringOptions.CENTER:
            self.shift_y(self.width / 2 - self.height / 2)

        if self.y_centering == CenteringOptions.BOTTOM:
            self.shift_y(self.width - self.height)

        self.rotation_angle = angle

    def rotate(self, angle):
        """Rotate the game object by a given angle.

         Args:
             angle (int): The change to the rotation angle in degrees.
         """
        self.set_rotation(self.rotation_angle + angle)

    def set_alpha(self, alpha):
        """Sets the alpha value of the game object.

         Args:
             alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
         """
        self.alpha = alpha

    def destroy(self):
        """Destroy the game object, hiding it in the current scene and notifying its parent if applicable."""
        if self.destroyed:
            return
        self.destroyed = True
        if self.parent is not None and hasattr(self.parent, "destroy_child"):
            self.parent.destroy_child(self)

    def add_child(self, child):
        """Adds a child game object to this game object's children, and notifies the child object of its new parent.

        Args:
            child (GameObject): The new child game object.
        """
        self.children.append(child)
        child.set_parent(self)

    def set_parent(self, parent):
        """Sets the parent of the game object and updates relative position attributes if applicable.

        Args:
            parent: The game object's new parent
        """
        self.parent = parent
        if not self.static and self.parent is not None:
            self.set_relative_x(self.x - self.parent.x)
            self.set_relative_y(self.y - self.parent.y)

    def add_multiple_children(self, children):
        """Adds multiple child game objects to this game object's children.

        Args:
            children (list): List of game object's to add as children.
        """
        for child in children:
            self.add_child(child)

    def destroy_child(self, child):
        """Destroys a specific child game object.

        Args:
            child (GameObject): The child game object to destroy.
        """
        if child in self.children:
            self.children.remove(child)

    def clear_children(self):
        """Removes all child game objects."""
        self.children = []

    def schedule_processing(self):
        """Schedules the game object and its children for processing in the game loop.
        The children are processed before the parent.

        Returns:
            list: List of game objects to be processed in the game loop.
        """
        items_to_be_processed = []
        for child in self.children:
            if hasattr(child, "update_position"):
                child.update_position()
            items_to_be_processed.extend(child.schedule_processing())

        items_to_be_processed.append(self)
        items_to_be_processed.sort(key=lambda x: x.z)
        return items_to_be_processed

    def process(self):
        """Processes the game object. Additional functionality to be implemented in child classes."""
        self.update_position()

    def update_position(self):
        """Updates the game object, updating its position relative to its parent if applicable."""
        if self.parent is not None and not self.static:
            self.update_position_relative_to_parent()

    def get_displayable_objects(self):
        """Gets a list of displayable game objects corresponding to the game object itself or its children.

        Returns:
            list: List of displayable game objects.
        """
        displayable_objects = []
        if self.destroyed:
            return displayable_objects

        if self.displayable:
            displayable_objects.append(self)

        for child in self.children:
            if hasattr(child, "get_displayable_objects"):
                displayable_objects.extend(child.get_displayable_objects())

        return displayable_objects


class Box(GameObject):
    """
    A class representing boxes, inheriting from the base class GameObject.

    Attributes:
        changed_recently (bool): Indicates if the box has been transformed since the last time it was displayed.
        text (str): The string to be displayed on the box
        text_offset (int): The space that should be between the buttons text (if any) and the edge of the box.
        text_color (tuple): The color of the text.
        font_size (int): The font size of the text.
        text_centering (string, string): The text centering mode. The first item corresponds to the horizontal
            placement, and the second the vertical placement.
        text_surface_id (int): The id corresponding to the font surface of the box.
        update_text_func (callable): The function responsible for updating the box text.
        surface_id (int): The id corresponding to the surface of the box.
    """

    def __init__(self, x=0, y=0, z=0, width=100, height=100, color=WHITE, alpha=255, source_image_id=None, text="",
                 text_offset=standard_text_offset, text_color=BLACK, font_size=40, resize_to_fit_text=False,
                 update_text_func=None, text_centering=(CenteringOptions.CENTER, CenteringOptions.CENTER), text_wrap=False,
                 x_centering=CenteringOptions.LEFT, y_centering=CenteringOptions.TOP, parent=None,
                 static=True, opaque=True,
                 include_border=False, name=None):
        """Initializes a Box object.

        Args:
            x (float): The x-coordinate of the box.
            y (float): The y-coordinate of the box.
            z (float): The z-coordinate of the box.
            width (float): The width of the box.
            height (float): The Height of the box.
            color (tuple): The color of the box
            alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
            source_image_id (int): The id of the source image of the box.
            text (str): The string to be displayed on the box.
            text_offset (int): The space that should be between the buttons text (if any) and the edge of the box.
            text_color (tuple): The color of the text.
            font_size (int): The font size of the text
            resize_to_fit_text (bool): Indicates whether the box should be resized in order to fit its text.
            text_centering (string, string): The text centering mode. The first item corresponds to the horizontal
            placement, and the second the vertical placement.
            x_centering (str): Indicates how the x-coordinate of the box should be centered when it is resized etc.
            y_centering (str): Indicates how the y-coordinate of the box should be centered when it is resized etc.
            update_text_func (callable): The function responsible for updating the box text.
            parent: The parent object to which this box is attached.
            static (bool): Indicates whether the box is static (does not move together with its parent).
            opaque (bool): Indicates whether the box is capable of blocking clicks.
            include_border (bool): Determines if the box should add a visual border or not.
            name (str): The name of the box.
        """
        super().__init__(x=x, y=y, z=z, width=width, height=height, alpha=alpha, parent=parent, static=static,
                         opaque=opaque, x_centering=x_centering, y_centering=y_centering,
                         displayable=True, name=name)

        self.color = color
        self.image_id = None
        self.source_image_id = source_image_id

        self.text = text
        self.text_offset = text_offset
        self.text_color = text_color
        self.font_size = font_size
        self.text_centering = text_centering
        self.text_wrap = text_wrap
        self.text_lines = []

        self.text_surface_id = None
        if resize_to_fit_text and self.text != "":
            self.resize_to_fit_text()

        if self.text != "":
            self.set_text(self.text)

        self.update_text_func = update_text_func

        if include_border:
            self.add_border()

        self.surface_id = game_engine.get_surface_manager().create_surface(self.width, self.height, self.alpha)
        self.set_alpha(self.alpha)
        self.update_surfaces()
        self.changed_recently = False

    def set_width(self, width):
        """Sets the width of the Box and updates the Box's image and surface,
        as well as its border if applicable.

        Args:
            width (float): The new width of the Box.
        """
        super().set_width(width)
        self.changed_recently = True
        if self.get_border() is not None:
            self.get_border().set_width(width)

    def set_height(self, height):
        """Sets the height of the Box and updates the Box's image and surface,
        as well as its border if applicable..

        Args:
            height (float): The new height of the Box.
        """
        super().set_height(height)
        self.changed_recently = True
        if self.get_border() is not None:
            self.get_border().set_height(height)

    def set_rotation(self, angle):
        """Sets the rotation angle of the Box and updates the Box's image and surface.

        Args:
            angle (int): The new rotation angle in degrees.
        """
        super().set_rotation(angle)
        self.changed_recently = True

    def set_image(self, new_source_image_id):
        """Sets the image of the Box by updating the source_image_id attribute, then rotates and scales the image.

         Args:
             new_source_image_id (int): The id of the new source image for the Box.
         """
        self.source_image_id = new_source_image_id
        self.update_image()

    def set_text(self, new_text):
        """Sets the text of the Box and updates the font surface id.

        Args:
            new_text (str): The new text for the Box.
        """
        self.text = new_text
        self.update_text_surface()

    def update_text_surface(self):
        """Updates the text surface of the box and truncates its text to fit the box."""
        self.truncate_text()
        self.text_surface_id = game_engine.get_surface_manager().create_font_surface(self.text, self.text_color,
                                                                                     self.font_size,
                                                                                     self.text_surface_id)

    def truncate_text(self):
        """Truncates the text of the box in order to fit the box."""
        self.text_lines = [self.truncate_text_line(self.text, not self.text_wrap)]
        if not self.text_wrap:
            self.text = self.text_lines[0]
            return
        number_of_dashes = 0
        font = game_engine.get_surface_manager().get_font(self.font_size)
        while True:
            occupied_height = self.text_line_height()
            allowed_height = self.height - 2 * self.text_offset
            height_one_line = pygame.font.Font.size(font, "testing")[1]
            final_line = occupied_height + height_one_line*2 >= allowed_height
            if occupied_height > allowed_height:
                if self.text_lines[-2][-1] == "-" and self.text_lines[-1][0] != " ":
                    self.text_lines[-2] = self.text_lines[-2][:-1] + self.text_lines[-1][0]
                self.text_lines = self.text_lines[:-1]
                self.text = "".join(self.text_lines)
                return
            total_text_length = len("".join(self.text_lines)) - number_of_dashes

            next_line = self.truncate_text_line(self.text[total_text_length:], final_line)
            if next_line == "":
                self.text = "".join(self.text_lines)
                return
            temp = self.text_lines[-1][-1]
            if temp != " " and temp != "-" and next_line[0] != " ":
                if self.text_lines[-1][-2] == " ":
                    self.text_lines[-1] = self.text_lines[-1][:-1] + " "
                else:
                    self.text_lines[-1] = self.text_lines[-1][:-1] + "-"
                number_of_dashes += 1
                self.text_lines.append(self.truncate_text_line(temp + next_line, final_line))
            else:
                self.text_lines.append(next_line)

    def text_line_height(self):
        """Calculates the used height for the box's text-lines.

        Returns:
            int: The calculated height.
        """
        height = 0
        font = game_engine.get_surface_manager().get_font(self.font_size)
        for line in self.text_lines:
            height += pygame.font.Font.size(font, line)[1]
        return height

    def truncate_text_line(self, text, final_line=False):
        """Truncates the supplied text line in order to fit the box in terms of its width.

        Args:
            text (string): The text that should be truncated.
            final_line (bool): Whether the text is located on the last line of the text-box.

        Returns:
            string: The truncated string.
        """
        font = game_engine.get_surface_manager().get_font(self.font_size)
        pruned_char = ""
        spaced = False
        while len(text) > 0:
            occupied_width = pygame.font.Font.size(font, text)[0]
            allowed_width = self.width - 2 * self.text_offset
            if occupied_width <= allowed_width:
                break
            words = text.split(" ")
            if len(words) == 1 or final_line:
                pruned_char = text[-1]
                text = text[:-1]
            else:
                text = " ".join(words[:-1])
                spaced = True
        if pruned_char == "-":
            text += pruned_char
        if spaced:
            text += " "
        return text

    def set_color(self, color):
        """Sets the color of the Box.

        Args:
            color (tuple): The new color for the Box.
        """
        self.color = color

    def set_alpha(self, alpha):
        """Sets the alpha value of the Box, and sets the alpha of the Box's surface to the same value.

        Args:
            alpha (int): The new alpha value.
        """
        self.alpha = alpha
        game_engine.get_surface_manager().fetch_surface(self.surface_id).set_alpha(self.alpha)

    def get_border(self):
        """Gets the border object associated with the button.

        Returns:
            Border: The border object of the button.
        """
        return utils.find_object_from_name(self.children, "button_border")

    def add_border(self):
        border = Border(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, parent=self,
                        name="button_border")
        self.add_child(border)

    def resize_to_fit_text(self, offset=None):
        """Adjusts the size of the Box to fit the text with an additional offset.

        Args:
            offset (int): The additional offset to apply.
        """
        if offset is None:
            offset = self.text_offset
        font = game_engine.get_surface_manager().get_font(self.font_size)
        required_width, required_height = pygame.font.Font.size(font, self.text)
        required_width += 2 * self.text_offset
        required_height += 2 * self.text_offset
        if required_width > self.width:
            self._resize_width(required_width, offset)

        if required_height > self.height:
            self._resize_height(required_height, offset)

    def _resize_width(self, required_width, offset):
        new_width = required_width + 2 * offset
        x_difference = new_width - self.width
        self.set_width(new_width)
        if self.x_centering == CenteringOptions.CENTER:
            self.shift_x(-x_difference / 2)
        elif self.x_centering == CenteringOptions.RIGHT:
            self.shift_x(-x_difference)

    def _resize_height(self, required_height, offset):
        new_height = required_height + 2 * offset
        y_difference = new_height - self.height
        self.set_height(new_height)
        if self.y_centering == CenteringOptions.CENTER:
            self.shift_y(-y_difference / 2)
        elif self.y_centering == CenteringOptions.RIGHT:
            self.shift_y(-y_difference)

    def update_surfaces(self):
        """Updates the surfaces of the box. First updates the image, and then the surface."""
        if self.source_image_id is not None:
            self.update_image()

        if self.text_surface_id is not None:
            self.update_text_surface()

        game_engine.get_surface_manager().transform_surface(self.surface_id, (self.width, self.height),
                                                            self.rotation_angle, self.surface_id)
        self.changed_recently = False

    def update_image(self):
        """Updates the image for the box, first by rotating the source image, and then scaling it."""
        self.image_id = game_engine.get_surface_manager().transform_image(self.source_image_id,
                                                                          (self.width, self.height),
                                                                          self.rotation_angle, self.image_id)

    def get_text_height(self):
        total_text_height = 0
        for line in self.text_lines:
            font_id = game_engine.get_surface_manager().create_temporary_font_surface(line, self.text_color,
                                                                                      self.font_size)
            font_surface = game_engine.get_surface_manager().fetch_font_surface(font_id)
            total_text_height += font_surface.get_height()
        return total_text_height

    def get_display_surface(self):
        """Return a tuple containing the surface to be displayed and the object's rect.

        Returns:
            tuple (pygame.Surface, pygame.Rect): The surface to be displayed and the object's rect.
        """
        if self.update_text_func is not None:
            self.set_text(self.update_text_func())

        if self.changed_recently:
            self.update_surfaces()

        if self.image_id is not None:
            game_engine.get_surface_manager().reset_surface(self.surface_id)
            image = game_engine.get_surface_manager().fetch_image(self.image_id)
            game_engine.get_surface_manager().fetch_surface(self.surface_id).blit(image, (0, 0))
        else:
            game_engine.get_surface_manager().fetch_surface(self.surface_id).fill(self.color)

        if self.text != "":
            horizontal_centering = self.text_centering[0]
            vertical_centering = self.text_centering[1]
            x, y = 0, 0
            total_text_height = self.get_text_height()

            if vertical_centering == CenteringOptions.TOP:
                y = self.text_offset

            elif vertical_centering == CenteringOptions.CENTER:
                y = (self.height - total_text_height) // 2

            elif vertical_centering == CenteringOptions.BOTTOM:
                y = self.height - total_text_height - self.text_offset

            for line in self.text_lines:
                font_id = game_engine.get_surface_manager().create_temporary_font_surface(line, self.text_color,
                                                                                          self.font_size)
                font_surface = game_engine.get_surface_manager().fetch_font_surface(font_id)

                if horizontal_centering == CenteringOptions.LEFT:
                    x = self.text_offset

                elif horizontal_centering == CenteringOptions.CENTER:
                    x = (self.width - font_surface.get_width()) / 2

                elif horizontal_centering == CenteringOptions.RIGHT:
                    x = self.width - self.text_offset - font_surface.get_width()

                else:
                    x = 0

                surface_blit_point = (x, y)

                game_engine.get_surface_manager().fetch_surface(self.surface_id).blit(font_surface, surface_blit_point)
                y += font_surface.get_height()

        return game_engine.get_surface_manager().fetch_surface(self.surface_id), self.get_rect()


class Border(GameObject):
    """A class for displaying a rectangular border.

    Attributes:
        thickness (int): The thickness of the border.
    """

    def __init__(self, x=0, y=0, z=1, width=100, height=100, color=BLACK, thickness=2, alpha=255, parent=None,
                 name=None):
        """Initialize a Border object.

        Args:
            x (float): The x-coordinate of the Border.
            y (float): The y-coordinate of the Border.
            z (float): The z-coordinate of the Border.
            width (float): The width of the Border.
            height (float): The height of the Border.
            color (tuple): The color of the Border (default is BLACK).
            thickness (int): The thickness of the Border.
            alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
            parent: The parent object to which this object is attached.
            name (str): The name of the Border.
        """
        super().__init__(x=x, y=y, z=z, width=width, height=height, alpha=alpha, parent=parent, static=False,
                         opaque=False, name=name)

        self.color = color
        self.thickness = thickness
        top_box = Box(x=self.x, y=self.y, z=z, width=self.width, height=self.thickness, color=self.color,
                      alpha=self.alpha,
                      parent=self, static=False, opaque=False, include_border=False, name="border_top_box")

        bottom_box = Box(x=self.x, y=self.y + self.height - self.thickness, z=z, width=self.width,
                         height=self.thickness, color=self.color, alpha=self.alpha, parent=self, static=False,
                         opaque=False, include_border=False, name="border_bottom_box")

        left_box = Box(x=self.x, y=self.y + self.thickness, width=self.thickness, z=z,
                       height=self.height - 2 * self.thickness, color=self.color, alpha=self.alpha, parent=self,
                       static=False, opaque=False, include_border=False, name="border_left_box")

        right_box = Box(x=self.x + self.width - self.thickness, y=self.y + self.thickness, z=z, width=self.thickness,
                        height=self.height - 2 * self.thickness, color=self.color, alpha=self.alpha, parent=self,
                        static=False, opaque=False, include_border=False, name="border_right_box")

        side_boxes = [top_box, bottom_box, left_box, right_box]

        for box in side_boxes:
            self.add_child(box)

    def set_width(self, width):
        """Sets the width of the Border and updates the side boxes to match.

        Args:
            width (float): The new width of the Border.
        """
        width_difference = width - self.width
        side_boxes = self.get_side_boxes()
        side_boxes[3].shift_x(width_difference)
        side_boxes[0].adjust_width(width_difference)
        side_boxes[1].adjust_width(width_difference)

        super().set_width(width)

    def set_height(self, height):
        """Sets the height of the Border and updates the side boxes to match.

        Args:
            height (float): The new height of the Border.
        """
        height_difference = height - self.height
        side_boxes = self.get_side_boxes()
        side_boxes[1].shift_y(height_difference)
        side_boxes[2].adjust_height(height_difference)
        side_boxes[3].adjust_height(height_difference)

        super().set_height(height)

    def set_color(self, color):
        """Sets the color of the Border.

        Args:
            color (tuple): The new color for the Border.
        """
        self.color = color

    def set_alpha(self, alpha):
        """Sets the alpha value of the Border.

        Args:
            alpha (int): The new alpha value.
        """
        self.alpha = alpha
        for box in self.get_side_boxes():
            box.set_alpha(self.alpha)

    def get_side_boxes(self):
        """Gets a list of side boxes that make up the Border.

        Returns:
            list: List of side boxes.
        """
        side_boxes = [x for x in self.children if isinstance(x, Box)]
        return side_boxes


class ButtonState:
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"


class ClickDetector:
    """A class dedicated to detecting clicks for buttons

    Attributes:
        rect (Pygame.rect): The rect inside which the click detector detects clicks.
        left_clicked (bool):
        left_clicked_long (bool):
        right_clicked (bool):
        right_clicked_long (bool):
        require_continuous_hovering (bool):
    """

    def __init__(self, rect):
        """Initialize the ClickDetector with the specified rectangle.

        Args:
            rect (pygame.Rect): The rect inside which the click detector detects clicks.
        """
        self.rect = rect

        self.left_clicked = False
        self.left_clicked_long = False

        self.right_clicked = False
        self.right_clicked_long = False

        self.require_continuous_hovering = True

    def _left_clicked(self):
        """Detects new left clicks.

        Returns:
            bool: True if the related rectangle is left-clicked, False otherwise.
        """
        left_mouse_down = environment.get_left_mouse_click_this_tick()
        mouse_over_rect = self.rect.collidepoint(environment.get_mouse_position())
        if left_mouse_down and mouse_over_rect and not environment.get_left_mouse_click_last_tick():
            return True

        return False

    def _left_clicked_long(self):
        """Detects long left clicks, that is if the mouse button continually being pressed.

        Returns:
            bool: True if the related rectangle is long left-clicked, False otherwise.
        """
        left_mouse_down = environment.get_left_mouse_click_this_tick()
        mouse_over_rect = self.rect.collidepoint(environment.get_mouse_position())
        excuse_non_hovering = not self.require_continuous_hovering and (self.left_clicked or self.left_clicked_long)

        if left_mouse_down and (mouse_over_rect or excuse_non_hovering):
            return True

        return False

    def _right_clicked(self):
        """Detects new right clicks.

        Returns:
            bool: True if the related rectangle is right-clicked, False otherwise.
        """
        right_mouse_down = environment.get_right_mouse_click_this_tick()
        mouse_over_rect = self.rect.collidepoint(environment.get_mouse_position())
        if right_mouse_down and mouse_over_rect and not environment.get_right_mouse_click_last_tick():
            return True

        return False

    def _right_clicked_long(self):
        """Detects long right clicks, that is if the mouse button continually being pressed.

        Returns:
            bool: True if the related rectangle is long right-clicked, False otherwise.
        """
        right_mouse_down = environment.get_right_mouse_click_this_tick()
        mouse_over_rect = self.rect.collidepoint(environment.get_mouse_position())
        excuse_non_hovering = not self.require_continuous_hovering and (self.right_clicked or self.right_clicked_long)

        if right_mouse_down and (mouse_over_rect or excuse_non_hovering):
            return True

        return False

    def update(self):
        """Updates the click detector's attributes based on the current mouse click events."""
        self.left_clicked = self._left_clicked()
        self.left_clicked_long = self._left_clicked_long()

        self.right_clicked_long = self._right_clicked_long()
        self.right_clicked = self._right_clicked()


class Button(Box):
    """A customizable button with various interactive features, such as click and hover events.

    Attributes:
        indicator_color (tuple): The color used for indicating if the button is hovered over or clicked.
        indicate_hover (bool): Indicates if the button should change appearance when it is hovered over.
        indicate_clicks (bool): Indicates if the button should change appearance when it is clicked.
        indicator_alpha (int): The alpha-value to be used on the indicator surface, if applicable.
        left_click_function (callable): The function to be called when the button is left-clicked.
        left_click_args (iterable): The arguments to be passed to the left click function.
        left_hold_function (callable): The function to be called when the button is left-held.
        left_hold_args (iterable): The arguments to be passed to the left hold function.
        right_click_function (callable): The function to be called when the button is right-clicked.
        right_click_args (iterable): The arguments to be passed to the right click function.
        right_hold_function (callable): The function to be called when the button is right-held.
        right_hold_args (iterable): The arguments to be passed to the right hold function.
        key_functions (dict): Dictionary mapping keys to functions and their arguments (default is None).
        external_process_function (callable): External function to be called during the button's processing
            (default is None).
        external_process_arguments: Arguments for the external process function (default is None).
    """

    # TODO: Change left_click_args etc. to args and kwargs.
    def __init__(self, x=0, y=0, z=1, width=200, height=120, color=GREY, indicator_color=WHITE, indicate_hover=True,
                 indicate_clicks=True, alpha=255, source_image_id=None, text="", text_offset=standard_text_offset,
                 font_size=40, text_color=BLACK, resize_to_fit_text=False,
                 text_centering=(CenteringOptions.CENTER, CenteringOptions.CENTER), text_wrap=False,
                 x_centering=CenteringOptions.LEFT, y_centering=CenteringOptions.TOP,
                 name=None, parent=None, include_border=True,
                 static=False, left_trigger_keys=None,
                 right_trigger_keys=None, left_click_function=None, left_click_args=None, left_hold_function=None,
                 left_hold_args=None, right_click_function=None, right_click_args=None, right_hold_function=None,
                 right_hold_args=None, key_functions=None, external_process_function=None,
                 external_process_arguments=None):
        """Creates a new button.

        Args:
            x (float): The x-coordinate of the button.
            y (float): The y-coordinate of the button.
            z (float): The z-coordinate of the button.
            width (float): The width of the button.
            height (float): The height of the button.
            color (tuple): The color of the button
            indicator_color (tuple): The color used for indicating if the button is hovered over or clicked.
            indicate_hover (bool): Indicates if the button should change appearance when it is hovered over.
            indicate_clicks (bool): Indicates if the button should change appearance when it is clicked.
            alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
            source_image_id (int): The id of the image used for the button (default is None).
            text (str): The text displayed on the button (default is an empty string).
            text_offset (int): The space that should be between the buttons text (if any) and the edge of the button.
            font_size (int): The font size of the text (default is 40).
            text_color: The color of the text (default is BLACK).
            resize_to_fit_text (bool): Indicates if the button should be resized in order to fit its text.
            text_centering (string, string): The text centering mode. The first item corresponds to the horizontal
            placement, and the second the vertical placement.
            x_centering (str): Indicates how the x-coordinate of the button should be centered when it is resized etc.
            y_centering (str): Indicates how the y-coordinate of the button should be centered when it is resized etc.
            include_border (bool): Determines if the button should have a border or not.
            name (str): The name of the button (default is None).
            parent: The parent object (default is None).
            static (bool): Indicates whether the object is static (does not move together with its parent).
            left_trigger_keys (list): List of keys triggering left-click events (default is None).
            right_trigger_keys (list): List of keys triggering right-click events (default is None).
            left_click_function (callable): The function to be called on left-click (default is None).
            left_click_args: The arguments for the left-click function (default is None).
            left_hold_function (callable): The function to be called while left-click is held (default is None).
            left_hold_args: The arguments for the left-hold function (default is None).
            right_click_function (callable): The function to be called on right-click (default is None).
            right_click_args: The arguments for the right-click function (default is None).
            right_hold_function: The function to be called while right-click is held (default is None).
            right_hold_args: The arguments for the right-hold function (default is None).
            key_functions (dict): Dictionary mapping keys to functions and their arguments (default is None).
            external_process_function (callable): External function to be called during the button's processing
                (default is None).
            external_process_arguments: Arguments for the external process function (default is None).
        """

        if external_process_arguments is None:
            self.external_process_arguments = []
        else:
            self.external_process_arguments = external_process_arguments

        if left_trigger_keys is None:
            self.left_trigger_keys = []
        else:
            self.left_trigger_keys = left_trigger_keys

        if right_trigger_keys is None:
            self.right_trigger_keys = []
        else:
            self.right_trigger_keys = right_trigger_keys

        if left_click_args is None:
            self.left_click_args = {}
        else:
            self.left_click_args = left_click_args

        if left_hold_args is None:
            self.left_hold_args = {}
        else:
            self.left_hold_args = left_hold_args

        if right_click_args is None:
            self.right_click_args = {}
        else:
            self.right_click_args = right_click_args

        if right_hold_args is None:
            self.right_hold_args = {}
        else:
            self.right_hold_args = right_hold_args

        if key_functions is None:
            self.key_functions = {}
        else:
            self.key_functions = key_functions
        super().__init__(x=x, y=y, z=z, width=width, height=height, color=color, alpha=alpha,
                         source_image_id=source_image_id, text=text, text_offset=text_offset, font_size=font_size,
                         text_color=text_color, resize_to_fit_text=resize_to_fit_text, text_centering=text_centering,
                         text_wrap=text_wrap,
                         x_centering=x_centering, y_centering=y_centering, parent=parent,
                         static=static, name=name, include_border=include_border)

        self.left_click_function = left_click_function
        self.left_hold_function = left_hold_function
        self.right_click_function = right_click_function
        self.right_hold_function = right_hold_function

        self.static = False

        self.external_process_function = external_process_function
        self.status = ButtonState.NORMAL

        self.click_detector = ClickDetector(self.get_rect())

        self.indicator_color = indicator_color
        self.indicate_hover = indicate_hover
        self.indicate_clicks = indicate_clicks
        self.indicator_alpha = 0

    def set_left_click_function(self, new_function, new_arguments=None):
        """Sets the function to be called when the button is left-clicked.

        Args:
            new_function: The new left-click function.
            new_arguments: The new arguments for the left-click function.
        """
        if new_arguments is None:
            new_arguments = []
        self.left_click_function = new_function
        self.left_click_args = new_arguments

    def set_left_hold_function(self, new_function, new_arguments=None):
        """Sets the function to be called when the button is left-held.

        Args:
            new_function (callable): The new left-hold function.
            new_arguments: The new arguments for the left-hold function.
        """
        if new_arguments is None:
            new_arguments = []
        self.left_hold_function = new_function
        self.left_hold_args = new_arguments

    def set_right_click_function(self, new_function, new_arguments=None):
        """Sets the function to be called when the button is right-clicked.

        Args:
            new_function (callable): The new right-clicked function.
            new_arguments: The new arguments for the right-clicked function.
        """
        if new_arguments is None:
            new_arguments = []
        self.right_click_function = new_function
        self.right_click_args = new_arguments

    def set_right_hold_function(self, new_function, new_arguments=None):
        """Sets the function to be called when the button is right-held.

        Args:
            new_function (callable): The new right-hold function.
            new_arguments: The new arguments for the right-hold function.
        """
        if new_arguments is None:
            new_arguments = []
        self.right_hold_function = new_function
        self.right_hold_args = new_arguments

    def get_external_process_function(self):
        """Gets the external process function.

        Returns:
            func: The external process function.
        """
        return self.external_process_function

    def set_external_process_function(self, new_function):
        """Sets a new external process function.

        Returns:
            new_function (callable): The new external process function.
        """
        self.external_process_function = new_function

    def get_external_process_arguments(self):
        """Gets the arguments for the external process function.

        Returns:
            list: List of arguments for the external process function.
        """
        return self.external_process_arguments

    def set_external_process_arguments(self, args):
        """Set the arguments for the external process function.

        Args:
            args (list): List of arguments for the external process function.
        """
        self.external_process_arguments = args

    def click_blocked(self, click_position):
        """Checks if the button click is blocked by other objects.

        Args:
            click_position: The position of the click.

        Returns:
            bool: True if the click is blocked, False otherwise.
        """
        blocking_objects_list = game_engine.get_scene_manager().get_current_scene().get_object_mask(self)
        for obj in blocking_objects_list:
            if obj.get_rect().collidepoint(click_position):
                return True
        return False

    def set_require_continuous_hovering(self, boolean):
        """Sets whether the button requires the mouse to be on it for button interaction.

        Args:
            boolean (bool): True if continuous hovering is required, False otherwise.
        """
        self.click_detector.require_continuous_hovering = boolean

    def check_button_presses(self):
        """Check for button presses/key presses and executes corresponding functions. Can execute any combination of
        different click events in the same tick."""
        mouse_position = environment.get_mouse_position()
        mouse_over_rect = self.get_rect().collidepoint(mouse_position)

        if not self.click_blocked(mouse_position):
            left_click_keys = utils.common_elements(environment.get_new_key_presses(), self.left_trigger_keys)
            button_left_clicked = self.click_detector.left_clicked or left_click_keys
            button_left_held = self.click_detector.left_clicked_long

            right_click_keys = utils.common_elements(environment.get_new_key_presses(), self.right_trigger_keys)
            button_right_clicked = self.click_detector.right_clicked or right_click_keys
            button_right_held = self.click_detector.right_clicked_long

            hovering = mouse_over_rect

        else:
            button_left_clicked = False
            button_left_held = False
            button_right_clicked = False
            button_right_held = False
            hovering = False

        self.status = ButtonState.HOVER

        key_functions, key_args = [], []
        for key in self.key_functions:
            if key in environment.get_new_key_presses():
                function = self.key_functions[key][0]
                args = self.key_functions[key][1]
                key_functions.append(function)
                key_args.append(args)

        if button_left_clicked and self.left_click_function is not None:
            self.status = ButtonState.PRESSED
            if isinstance(self.left_click_args, dict):
                self.left_click_function(**self.left_click_args)
            else:
                self.left_click_function(*self.left_click_args)

        if button_left_held and self.left_hold_function is not None:
            self.status = ButtonState.PRESSED
            if isinstance(self.left_hold_args, dict):
                self.left_hold_function(**self.left_hold_args)
            else:
                self.left_hold_function(*self.left_hold_args)

        if button_right_clicked and self.right_click_function is not None:
            self.status = ButtonState.PRESSED

            if isinstance(self.right_click_args, dict):
                self.right_click_function(**self.right_click_args)
            else:
                self.right_click_function(*self.right_click_args)

        if button_right_held and self.right_hold_function is not None:
            self.status = ButtonState.PRESSED
            if isinstance(self.right_hold_args, dict):
                self.right_hold_function(**self.right_hold_args)
            else:
                self.right_hold_function(*self.right_hold_args)

        if len(key_functions) != 0:
            for function, args in zip(key_functions, key_args):
                if isinstance(args, dict):
                    function(**args)
                else:
                    function(*args)

        if not hovering:
            self.status = ButtonState.NORMAL

    def process(self):
        """Process the button, updating its click_detector checking for click-events and updating its color."""
        if self.external_process_function is not None:
            self.external_process_function(*self.external_process_arguments)

        super().process()

        self.click_detector.update()

        self.check_button_presses()

        if self.status == ButtonState.PRESSED and self.indicate_clicks:
            self.indicator_alpha = 100
        elif self.status == ButtonState.PRESSED:
            if self.indicate_hover:
                self.indicator_alpha = 80
        elif self.status == ButtonState.HOVER and self.indicate_hover:
            self.indicator_alpha = 80

        else:
            self.indicator_alpha = 0

    def get_display_surface(self):
        """Return a tuple containing the surface to be displayed and the object's rect.

        Returns:
            tuple (pygame.Surface, pygame.Rect): The surface to be displayed and the object's rect.
        """
        surf, rect = super().get_display_surface()

        if self.indicator_alpha != 0:
            temporary_surface_id = game_engine.get_surface_manager().create_temporary_surface(self.width,
                                                                                              self.height,
                                                                                              self.indicator_alpha)
            indicator_surface = game_engine.get_surface_manager().fetch_surface(temporary_surface_id)
            indicator_surface.fill(self.indicator_color)
            surf.blit(indicator_surface, (0, 0))

        return surf, rect


class MobileButton(Button):
    """A class for a button that can be moved using the mouse.

    Attributes:
        moving (bool): Indicates whether the button is currently moving.
        click_x (int): The x-coordinate of the mouse click in the button's coordinate system.
        click_y (int): The y-coordinate of the mouse click in the button's coordinate system.
    """

    def __init__(self, x=0, y=0, z=1, width=200, height=120, color=(100, 100, 100), indicator_color=WHITE,
                 indicate_hover=True,
                 indicate_clicks=False, alpha=255, static=False,
                 source_image_id=None, text="", font_size=40,
                 text_color=BLACK, text_centering=(CenteringOptions.CENTER, CenteringOptions.CENTER), x_centering=CenteringOptions.LEFT,
                 y_centering=CenteringOptions.TOP,
                 include_border=True, name=None, parent=None,
                 left_trigger_keys=None, left_hold_function=None,
                 left_hold_args=None, right_trigger_keys=None,
                 right_click_function=None, right_click_args=None, right_hold_function=None, right_hold_args=None,
                 key_functions=None, external_process_function=None, external_process_arguments=None):
        """Creates a new mobile button with movement support.

        Args:
            x (float): The x-coordinate of the button.
            y (float): The y-coordinate of the button.
            z (float): The z-coordinate of the button.
            width (float): The width of the button.
            height (float): The height of the button.
            color (tuple): The color of the button.
            indicator_color (tuple): The color to be used to indicate if the button is hovered over or pressed.
            indicate_hover (bool): Indicates if the button should change appearance when it is hovered over.
            indicate_clicks (bool): Indicates if the button should change appearance when it is clicked.
            alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
            static (bool): Indicates whether the button is static (does not move together with its parent).
            source_image_id (int): The id of the image used for the button (default is None).
            text (str): The text displayed on the button (default is an empty string).
            font_size (int): The font size of the text (default is 40).
            text_color: The color of the text (default is BLACK).
            text_centering (string, string): The text centering mode. The first item corresponds to the horizontal
            placement, and the second the vertical placement.
            x_centering (str): Indicates how the x-coordinate of the button should be centered when it is resized etc.
            y_centering (str): Indicates how the y-coordinate of the box should be centered when it is resized etc.
            include_border (bool): Determines if the button should have a border or not.
            name (str): The name of the button (default is None).
            parent: The parent object (default is None).
            left_trigger_keys (list): List of keys triggering left-click events (default is None).
            right_trigger_keys (list): List of keys triggering right-click events (default is None).
            left_hold_function: The function to be called while left-click is held (default is None).
            left_hold_args: The arguments for the left-hold function (default is None).
            right_click_function (callable): The function to be called on right-click (default is None).
            right_click_args: The arguments for the right-click function (default is None).
            right_hold_function: The function to be called while right-click is held (default is None).
            right_hold_args: The arguments for the right-hold function (default is None).
            key_functions (dict): Dictionary mapping keys to functions and their arguments (default is None).
            external_process_function (callable): External function to be called during the button's processing
                (default is None).
            external_process_arguments: Arguments for the external process function (default is None).
        """

        self.moving = False
        self.click_x = None
        self.click_y = None
        super().__init__(x=x, y=y, z=z, width=width, height=height, color=color, indicator_color=indicator_color,
                         indicate_hover=indicate_hover, indicate_clicks=indicate_clicks, alpha=alpha,
                         source_image_id=source_image_id,
                         text=text, font_size=font_size, text_color=text_color, text_centering=text_centering,
                         x_centering=x_centering, y_centering=y_centering,
                         include_border=include_border,
                         name=name, parent=parent, static=static,
                         left_trigger_keys=left_trigger_keys, right_trigger_keys=right_trigger_keys,
                         left_click_function=self.start_movement, left_hold_function=left_hold_function,
                         left_hold_args=left_hold_args,
                         right_click_function=right_click_function, right_click_args=right_click_args,
                         right_hold_function=right_hold_function, right_hold_args=right_hold_args,
                         key_functions=key_functions, external_process_function=external_process_function,
                         external_process_arguments=external_process_arguments)
        super().set_require_continuous_hovering(False)

    def set_x(self, x):
        """Sets the x-position of the MobileButton, and updates the click-position.

        Args:
            x (float): The new x-position.
        """
        super().set_x(x)
        self.update_click_position()

    def set_y(self, y):
        """Sets the y-position of the MobileButton, and updates the click-position.

        Args:
            y (float): The new y-position.
        """
        super().set_y(y)
        self.update_click_position()

    def update_position(self):
        """Updates the mobile buttons position."""

        if not self.click_detector.left_clicked_long:
            self.moving = False
            self.click_x, self.click_y = None, None
        else:
            self.move()
        super().update_position()

    def move(self):
        """Handles the movement of the mobile button."""
        if not self.moving:
            return
        mouse_position = environment.get_mouse_position()
        self.set_pos(mouse_position[0] - self.click_x, mouse_position[1] - self.click_y)

    def start_movement(self):
        """Starts the movement of the mobile button."""
        self.moving = True
        self.update_click_position()

    def update_click_position(self):
        """Updates the click position of the MobileButton."""
        mouse_position = environment.get_mouse_position()
        self.click_x, self.click_y = mouse_position[0] - self.x, mouse_position[1] - self.y


class InputTypes:
    """A class for storing possible character types and their associated allowed characters."""
    NUMBER = "0123456789"
    LOWERCASE = "abcdefghijklmnopqrstuvwxyzåäö"
    UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ"
    TEXT = LOWERCASE + UPPERCASE
    ANY = ""


class InputField(Button):
    """A class for a text-field, that can be left-clicked in order to modify its text with the keyboard.

    Attributes:
        is_selected (bool): Indicates if the InputField is currently selected, and can be written to.
        fixed_text (str): The part of the InputField text that cannot be changed by input.
        text_buffer (str): The part of the InputField text that can be changed by input.
        allowed_input_type (str): A string containing all allowed characters.
        return_key_function (callable): The function to be executed when return is pressed and input field is selected.
        return_key_args (iterable): The arguments for the return key function.
    """

    def __init__(self, x=0, y=0, z=1, width=200, height=120, color=GREY, indicate_hover=False, indicate_clicks=True,
                 alpha=255, text="", font_size=20, text_color=BLACK, initial_text_buffer="",
                 allowed_input_type=InputTypes.ANY, text_centering=(CenteringOptions.LEFT, CenteringOptions.CENTER), text_wrap=False,
                 name=None, include_border=True, static=False, return_key_function=None, return_key_args=None):
        """Initializes an InputField object.

        Args:
            x (float): The x-coordinate of the InputField.
            y (float): The y-coordinate of the InputField.
            z (float): The z-coordinate of the InputField.
            width (float): The width of the InputField.
            height (float): The height of the InputField.
            color (tuple): The color of the InputField
            indicate_hover (bool): Indicates if the InputField should change appearance when it is hovered over.
            indicate_clicks (bool): Indicates if the InputField should change appearance when it is clicked.
            alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
            text (str): The text displayed on the InputField (default is an empty string).
            font_size (int): The font size of the text (default is 40).
            text_color: The color of the text (default is BLACK).
            initial_text_buffer (str): The initial text_buffer of the InputField
            text_centering (string, string): The text centering mode. The first item corresponds to the horizontal
            placement, and the second the vertical placement.
            allowed_input_type (str): The allowed input type of the InputField.
            name (str): The name of the InputField (default is None).
            include_border (bool): Determines if the button should have a border or not.
            static (bool): Indicates whether the InputField is static (does not move together with its parent).
            return_key_function (callable): The function to be executed when return is pressed and input field is selected.
            return_key_args (iterable): The arguments for the return key function.
        """
        super().__init__(x=x, y=y, z=z, width=width, height=height, color=color,
                         indicate_hover=indicate_hover,
                         indicate_clicks=indicate_clicks, alpha=alpha, font_size=font_size,
                         text_color=text_color, text_centering=text_centering, text_offset=standard_text_offset*2,
                         text_wrap=text_wrap,
                         name=name, include_border=include_border, static=static,
                         left_click_function=self.create_input_detector)

        self.is_selected = False
        self.update_text = True

        self.fixed_text = text
        self.text_buffer = initial_text_buffer
        self.update_text_from_buffer()

        self.allowed_input_type = allowed_input_type

        self.backspace_counter = 0
        self.backspace_timer = 0

        self.return_key_function = return_key_function
        self.return_key_args = return_key_args

    def create_input_detector(self):
        """Creates a new InputDetector object."""
        self.is_selected = True
        game_engine.start_text_input()

    def write(self):
        """Writes text to the InputDetectors parents text_buffer."""
        if environment.input_event is None:
            return
        self.update_text = True
        self.append_text(environment.input_event)
        environment.input_event = None

    def append_text(self, text):
        """Appends text to the text_buffer.

        Args:
            text (str): The text to be added to the text_buffer.
        """
        if not self.verify_input_type(text):
            return
        self.text_buffer += text

    def verify_input_type(self, new_input):
        """Verifies the input against the allowed input_type.

        Args:
            new_input (str): The input.

        Returns:
            bool: True if the input is allowed, False otherwise.
        """
        if self.allowed_input_type == InputTypes.ANY:
            return True
        return new_input in self.allowed_input_type

    def update_text_from_buffer(self):
        """Updates the InputFields text from the fixed_text and the text_buffer."""
        self.set_text(self.fixed_text + self.text_buffer)
        allowed_text_buffer_length = len(self.text) - len(self.fixed_text)
        number_of_extra_dashes = 0
        for i, line in enumerate(self.text_lines[:-1]):
            if line[-1] == "-" and self.text_lines[i+1] != " ":
                number_of_extra_dashes += 1
        self.text_buffer = self.text_buffer[:allowed_text_buffer_length - number_of_extra_dashes]

    def check_for_input(self):
        self.write()

        keys_pressed = environment.get_pressed_keys_this_tick()

        new_backspace_press = False
        for event in game_engine.environment.events:
            if event.type == pygame.KEYUP and pygame.key.name(event.key) == Keys.BACKSPACE:
                self.backspace_counter = 0
            if event.type == pygame.KEYDOWN and pygame.key.name(event.key) == Keys.BACKSPACE:
                new_backspace_press = True

        if Keys.BACKSPACE in keys_pressed:
            self.backspace(new_press=new_backspace_press)
            return

        if Keys.RETURN in keys_pressed:
            self.press_return()
            return

    def backspace(self, new_press=False):
        """Handels the backspace key event."""
        if self.backspace_counter > 0:
            if time.time() - self.backspace_timer > 0.02:  # Hard-coded value.
                self.backspace_counter -= 2
                self.backspace_timer = time.time()
            return
        self.update_text = True
        self.text_buffer = self.text_buffer[:-1]
        self.backspace_timer = time.time()
        if new_press:
            self.backspace_counter = 8  # Hard-coded value.
        else:
            self.backspace_counter = 2  # Hard-coded value.

    def press_return(self):
        """Executes the return key function if set."""
        if self.return_key_function is not None:
            self.return_key_function(*self.return_key_args)

    def process(self):
        """Processes the InputField, updating its text if it is currently selected."""
        super().process()

        if utils.detect_external_clicks([self.get_rect()]):
            game_engine.stop_text_input()
            self.is_selected = False

        self.check_for_input()

        if self.is_selected and self.update_text:
            self.update_text_from_buffer()
            self.update_text = False

    def get_display_surface(self):
        """Return a tuple containing the surface to be displayed and the object's rect.

        Returns:
            tuple: The surface to be displayed and the object's rect.
        """
        if self.is_selected:
            self.set_color(LIGHT_GREY)
        else:
            self.set_color(GREY)
        return super().get_display_surface()


class Keys:
    """A class for storing possible special key-presses."""
    SPACE = "space"
    RETURN = "return"
    BACKSPACE = "backspace"
    LSHIFT = "left shift"


class Overlay(GameObject):
    """A graphical overlay with a customizable appearance and optional close button.

    Attributes:
        Inherits all attributes from the GameObject class.
    """

    def __init__(self, x=0, y=0, z=2, width=1540, height=760, alpha=255, static=True, name=None, background_color=WHITE,
                 close_button_size=30, close_button_offset=5, include_border=True, include_close_button=True,
                 parent=None,
                 external_process_function=None, external_process_arguments=None):
        """Creates a new overlay with an optional close button.

         Args:
             x (float): The x-coordinate of the overlay.
             y (float): The y-coordinate of the overlay.
             z (float): The z-coordinate of the overlay.
             width (float): The width of the overlay.
             height (float): The height of the overlay.
             alpha (int): The alpha value, ranging from 0 (transparent) to 255 (opaque).
             static (bool): Indicates whether the overlay is static (does not move together with its parent).
             name (str): The name of the overlay.
             background_color (tuple): The color of the overlay background.
             close_button_size (float): Size of the close button on the overlay.
             close_button_offset (float): Offset of the close button from the top-right corner of the overlay.
             include_border (bool): Determines if a border should be added to the edge of the overlay box.
             parent: The parent object to which this overlay is attached.
             external_process_function (callable): External function to be called during the overlay's processing.
             external_process_arguments: Arguments for the external process function.
         """

        super().__init__(x=x, y=y, z=z, width=width, height=height, parent=parent, static=static,
                         alpha=alpha, opaque=False, name=name)
        if external_process_arguments is None:
            self.external_process_arguments = []
        else:
            self.external_process_arguments = external_process_arguments
        self.external_process_function = external_process_function

        box = Box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, color=background_color,
                  alpha=self.alpha, static=False, name="overlay_box", include_border=include_border)
        self.add_child(box)

        self.parent = parent

        if include_close_button:
            self.close_button_size = close_button_size
            self.close_button_offset = close_button_offset
            close_button = Button(x=self.x + self.width - close_button_size - close_button_offset,
                                  y=self.y + close_button_offset, z=self.z, width=close_button_size,
                                  height=close_button_size,
                                  source_image_id=file_op.load_image("Images/close_button.png"), font_size=15,
                                  parent=self,
                                  left_click_function=self.destroy, left_trigger_keys=["escape"],
                                  name="close_button")
            self.add_child(close_button)

    def get_rect(self):
        """Gets the rectangular area occupied by the overlay.

         Returns:
             pygame.Rect: The rectangular area of the overlay.
         """
        return self.get_box().get_rect()

    def get_box(self):
        """Gets the underlying box object of the overlay.

        Returns:
            Box: The box object of the overlay.
        """
        return utils.find_object_from_name(self.children, "overlay_box")

    def get_buttons(self):
        """Gets a list of button objects present in the overlay.

        Returns:
            list: List of Button objects in the overlay.
        """
        return utils.find_objects_from_type(self.children, Button)

    def set_background_color(self, color):
        """Sets the background color of the overlay.

        Args:
            color (tuple): The color to set as the background color.
        """
        self.get_box().set_color(color)

    def set_background_image(self, source_id):
        """Sets the background image of the overlay.

        Args:
            source_id (int): The source ID of the new background image.
        """
        self.get_box().set_image(source_id)

    def process(self):
        """Processes the overlay, including external processing and the standard processing routine."""
        if self.external_process_function is not None:
            self.external_process_function(*self.external_process_arguments)

        super().process()


class ConfirmationOverlay(Overlay):
    """A graphical overlay with Yes and No buttons.

    Attributes:
        Inherits all attributes from the Overlay class.
    """

    def __init__(self, x=0, y=0, yes_button_function=None, args=None):
        """
        Creates the Confirmation Overlay object.
        Args:
            x (float): The x-coordinate of the overlay.
            y (float): The y-coordinate of the overlay.
            yes_button_function (func): The function to be executed when the yes-button is pressed.
            args: The arguments to pass to the function.
        """
        z = 10
        width = 300
        height = 150
        if x is None:
            x = environment.get_mouse_position()[0] - width // 2
        if y is None:
            y = environment.get_mouse_position()[1] - height // 2
        super().__init__(x=x, y=y, z=z,
                         width=width, height=height, name="confirmation_overlay",
                         external_process_function=utils.destroy_on_external_clicks)

        allowed_click_rects = [self, [self.get_rect()]]
        self.external_process_arguments = allowed_click_rects

        close_button = utils.find_object_from_name(self.get_buttons(), "close_button")
        self.destroy_child(close_button)

        button_width = 70
        button_height = 50
        offset = 7
        font_size = 30
        text_box = Box(y=self.y + offset, z=self.z, static=False, text="Are you sure?", resize_to_fit_text=True,
                       parent=self)
        text_box.set_pos(self.x + (self.width - text_box.width) // 2, text_box.y)
        self.add_child(text_box)
        yes_button = Button(width=button_width, height=button_height,
                            text="Yes", text_offset=5, font_size=font_size, resize_to_fit_text=True,
                            left_click_function=utils.execute_multiple_functions,
                            left_click_args=[[self.destroy, yes_button_function], [[], args]],
                            left_trigger_keys=["return"], static=False, parent=self, name="overlay_yes_button")
        no_button = Button(width=button_width,
                           height=button_height,
                           text="No", text_offset=5, font_size=font_size, resize_to_fit_text=True,
                           left_click_function=self.destroy, left_trigger_keys=["escape"], static=False, parent=self,
                           name="overlay_no_button")

        buttons = [yes_button, no_button]
        number_of_buttons = len(buttons)
        x_offset = (self.width - number_of_buttons * button_width) // (number_of_buttons + 1)
        for i, button in enumerate(buttons):
            button.set_z(self.z)
            self.add_child(button)
            button.set_pos(self.x + (i + 1) * x_offset + i * button_width,
                           y=self.y + self.height - offset - button_height)
