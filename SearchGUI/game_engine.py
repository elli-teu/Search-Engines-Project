from constants import *
import os
import pickle
import utility_functions as utils
import surface_manager

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


class Environment:
    """Initializes the Environment instance.

    The Environment manages various aspects of the game environment, such as the display window, mouse events,
    and screen dimensions.

    Attributes:
        scale_factor (int): The scaling factor for the game window.
        window (pygame.Surface): The resizable game window.
        key_press (str): The key pressed during the current tick.
        width (int): The width of the game window.
        height (int): The height of the game window.
        screen_id (int): The id of the main drawing surface for the game.
        clock (pygame.time.Clock): The Pygame clock for managing frame rates.
        standard_offset (int): A standard offset value used in various calculations.
        events_last_tick (dict): Dictionary storing mouse and key events from the last tick.
        events_this_tick (dict): Dictionary storing mouse and key events for the current tick.
    """

    def __init__(self):
        """Creates the Environment object."""
        # TODO: Improve event structure.
        self.scale_factor = 1
        self.window = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        self.key_press = None
        self.width = pygame.display.Info().current_w
        self.height = pygame.display.Info().current_h
        self.screen_id = get_surface_manager().create_surface(self.get_width(), self.get_height(), alpha=255)
        self.clock = pygame.time.Clock()
        self.standard_offset = 15
        self.events_last_tick = {"left_mouse_button": False, "right_mouse_button": False, "pressed_keys": []}
        self.events_this_tick = {"left_mouse_button": False, "right_mouse_button": False, "pressed_keys": []}
        self.input_event = None
        self.events = []

    def get_width(self):
        """Gets the width of the game window.

        Returns:
            int: The width of the game window.
        """
        return self.width

    def set_width(self, width):
        """Sets the width of the screen.

        Args:
            width (int): The new width of the screen.
        """
        self.width = round(width)

    def get_height(self):
        """Gets the height of the game window.

        Returns:
            int: The height of the game window.
        """
        return self.height

    def set_height(self, height):
        """Sets the height of the screen.

        Args:
            height (int): The new height of the screen.
        """
        self.height = round(height)

    def get_resolution(self):
        """Gets the current resolution of the screen.

        Returns:
            tuple: The resolution of the screen in as a (width, height) tuple.
        """
        return self.get_width(), self.get_height()

    def set_resolution(self, resolution):
        """Sets the resolution of the screen.

        Args:
            resolution (tuple): The new resolution of the screen (width, height).
        """
        self.set_width(resolution[0])
        self.set_height(resolution[1])
        self.screen_id = get_surface_manager().create_surface(self.get_width(), self.get_height())

    def get_screen(self):
        """Gets the screen surface belonging to the environment.

        Returns:
            pygame.Surface: The surface object belonging to the environment.
        """
        return get_surface_manager().fetch_surface(self.screen_id)

    def get_mouse_position(self):
        """Returns the current mouse position in screen-space coordinates, not window-space.

        Returns:
            tuple: A tuple of floats representing the mouse position.
        """
        x, y = pygame.mouse.get_pos()
        window_width = pygame.display.Info().current_w
        window_height = pygame.display.Info().current_h
        scale_x = self.get_screen().get_width() / window_width
        scale_y = self.get_screen().get_height() / window_height
        return round(x * scale_x), round(y * scale_y)

    def set_events_this_tick(self, events):
        """Sets the recorded events for the current tick.

        Args:
            events (dict): A dictionary containing mouse and key events.

        """
        self.events_this_tick = events

    def set_events_last_tick(self, events):
        """Sets the recorded events for the last tick.

        Args:
            events (dict): A dictionary containing mouse and key events.

        """
        self.events_last_tick = events

    def get_events_this_tick(self):
        """Gets the events dictionary for the current tick.

        Returns:
            dict: A dictionary containing recorded mouse and key events for the current tick.

        """
        return self.events_this_tick

    def get_events_last_tick(self):
        """Gets the events dictionary for the last tick.

        Returns:
            dict: A dictionary containing recorded mouse and key events for the last tick.

        """
        return self.events_last_tick

    def get_left_mouse_click_this_tick(self):
        """Returns whether the left mouse button was clicked during the current tick.

        Returns:
            bool: True if the left mouse button was clicked, False otherwise.

        """
        return self.events_this_tick["left_mouse_button"]

    def get_right_mouse_click_this_tick(self):
        """Returns whether the right mouse button was clicked during the current tick.

        Returns:
            bool: True if the right mouse button was clicked, False otherwise.

        """
        return self.events_this_tick["right_mouse_button"]

    def get_left_mouse_click_last_tick(self):
        """Returns whether the left mouse button was clicked during the last tick.

        Returns:
            bool: True if the left mouse button was clicked last tick, False otherwise.

        """
        return self.events_last_tick["left_mouse_button"]

    def get_right_mouse_click_last_tick(self):
        """Returns whether the right mouse button was clicked during the last tick.

        Returns:
            bool: True if the right mouse button was clicked last tick, False otherwise.

        """
        return self.events_last_tick["right_mouse_button"]

    def get_new_key_presses(self):
        """Returns whether the key that was pressed during the current tick, if any.

        Returns:
            str or None: The string representing the key that was pressed this tick, or None if no key was pressed.
        """
        new_key_presses = []
        keys_down = self.get_pressed_keys_this_tick()
        old_keys_down = self.get_pressed_keys_last_tick()
        for key in keys_down:
            if key not in old_keys_down:
                new_key_presses.append(key)
        return new_key_presses

    def get_pressed_keys_this_tick(self):
        return self.events_this_tick["pressed_keys"]

    def get_pressed_keys_last_tick(self):
        return self.events_last_tick["pressed_keys"]

    def handle_events(self):
        """Checks for detected pygame events, such as if the user tries to close the program window or if the
        user clicks the mouse or presses any keys.

        Returns:
            bool: True if the program should continue running, False if the user closed the window.
        """
        is_running = True
        self.key_press = None
        pressed_keys = self.get_pressed_keys_last_tick().copy()
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                pressed_keys.append(pygame.key.name(event.key))
            elif event.type == pygame.KEYUP:
                pressed_keys.remove(pygame.key.name(event.key))
            elif event.type == pygame.TEXTINPUT:
                self.input_event = event.text

        left_mouse_down = pygame.mouse.get_pressed(num_buttons=3)[0]
        right_mouse_down = pygame.mouse.get_pressed(num_buttons=3)[2]
        self.set_events_this_tick({"left_mouse_button": left_mouse_down, "right_mouse_button": right_mouse_down,
                                   "pressed_keys": pressed_keys})
        return is_running

    def draw_screen(self):
        """Draws the screen by scaling the surface and updating the window display."""
        screen = get_surface_manager().fetch_surface(self.screen_id)
        resized_screen = pygame.transform.smoothscale(screen, self.window.get_rect().size)
        self.window.blit(resized_screen, (0, 0))
        pygame.display.flip()


class GameState:
    """An object representing the current game state.

    Attributes:
        surface_manager (SurfaceManager): Manager for surfaces, images, fonts, and their metadata.
        surface_objects (dict): A dictionary relating surface ids and SurfaceHelper objects.
        current_max_id (int): The current maximum ID used for surface and image identification.
        scene_manager (SceneManager): Manager for scenes and scene transitions.
        tick_manager (TickManager): TickManager object for storing start and end of tick functions.
    """

    def __init__(self):
        """Creates a GameState object."""
        self.surface_manager = surface_manager.SurfaceManager()
        self.current_max_id = self.surface_manager.current_max_id
        self.surface_objects = self.surface_manager.surface_objects
        self.image_path_id_dict = self.surface_manager.image_path_id_dict = {}

        self.scene_manager = SceneManager()

        self.tick_manager = TickManager()

    def load_from_surface_manager(self):
        """Load surface-related attributes from the SurfaceManager."""
        self.current_max_id = self.surface_manager.current_max_id
        self.surface_objects = self.surface_manager.surface_objects
        self.image_path_id_dict = self.surface_manager.image_path_id_dict

    def get_savable_copy(self):
        """Creates a copy of the GameState object that can be saved.

        Returns:
            GameState: A new GameState object with surface-related attributes prepared for saving.
        """
        new_game_state = GameState()
        new_game_state.surface_manager = self.surface_manager.copy()
        new_game_state.scene_manager = self.scene_manager
        new_game_state.load_from_surface_manager()
        for surface_object in new_game_state.surface_objects.values():
            surface_object.prepare_for_saving()
        return new_game_state


class TickManager:
    """This class serves as a data storage for functions and arguments to be executed
    at the start and end of each game tick.

    Attributes:
        start_of_tick_functions (list): List to store functions to be executed at the start of a tick.
        start_of_tick_arguments (list): List to store arguments for functions to be executed at the start of a tick.
        end_of_tick_functions (list): List to store functions to be executed at the end of a tick.
        end_of_tick_arguments (list): List to store arguments for functions to be executed at the end of a tick.
    """

    def __init__(self):
        """Initialize the TickManager object."""
        self.start_of_tick_functions = []
        self.start_of_tick_arguments = []
        self.end_of_tick_functions = []
        self.end_of_tick_arguments = []


class SceneManager:
    """A class for managing the scenes.

    Attributes:
        scenes (dict): A dictionary to store scenes by name.
        current_scene: The currently active scene.
    """

    def __init__(self):
        """Initializes the SceneManager."""
        self.scenes = {}
        self.current_scene = None

    def get_current_scene(self):
        """Get the currently active scene.

        Returns:
            Scene: The currently active scene.
        """
        return self.current_scene

    def set_current_scene(self, new_scene):
        """Set the currently active scene.

        Args:
            new_scene (Scene): The scene to set as the active scene.
        """
        self.current_scene = new_scene

    def create_scene(self, scene):
        """Create and change to a new scene.

        Args:
            scene (Scene): THe new scene.

        Returns:
            Scene: The newly created scene.
        """
        if scene.name in self.scenes and self.scenes[scene.name].persistent:
            return self.change_scene_by_name(scene.name)

        scene.create_scene()
        return self.change_scene(scene)

    def change_scene_by_name(self, name):
        """Change to a scene by using its name.

        Args:
            name (str): The name of the scene to change to.

        Returns:
            Scene: The newly active scene.
        """
        return self.change_scene(self.scenes[name])

    def change_scene(self, scene):
        """Change to a new scene.

        Args:
            scene (Scene): The scene to change to.

        Returns:
            Scene: The newly active scene.
        """
        self.clear_current_scene()
        self.set_current_scene(scene)
        self.scenes[scene.name] = scene
        return scene

    def clear_current_scene(self):
        """Clear the currently active scene, if it is not persistent."""
        if self.get_current_scene() is not None and not self.get_current_scene().persistent:
            self.get_current_scene().clear()

    def schedule_scene_change(self, scene):
        """Schedule a scene change at the start of the next tick.

        Args:
            scene (Scene): The new scene.
        """

        schedule_start_of_tick_function(self.create_scene, [scene])


class Scene:
    """A class representing a scene in the application.

    Attributes:
        name (str): The name of the scene.
        objects (list): A list of objects within the scene. Does not include all objects, only the root objects, so
        these objects can have
            children etc.
        processing_order (list): The order in which objects are processed.
        display_order (list): The order in which objects are displayed.
        background_color (tuple): The background color of the scene.
        persistent (bool): Whether the scene is persistent across scene changes.
    """

    def __init__(self, name):
        """Initialize a Scene object.

        Args:
            name (str): The name of the scene.
        """
        self.name = name
        self.objects = []
        self.processing_order = []
        self.preliminary_display_order = []
        self.display_order = []
        self.background_color = WHITE
        self.persistent = False

    def get_objects(self):
        """Get the list of root objects in the scene.

        Returns:
            list: The list of root objects in the scene.
        """
        return self.objects

    def add_object(self, obj):
        """Add a root object to the scene.

        Args:
            obj: The object to add.
        """
        self.objects.append(obj)

    def remove_object(self, obj):
        """Remove a root object from the scene.

        Args:
            obj: The object to remove.
        """
        if obj in self.objects:
            self.objects.remove(obj)

    def add_multiple_objects(self, object_list):
        """Add multiple root objects to the scene.

        Args:
            object_list (list): The list of root objects to add to the scene.
        """
        self.objects.extend(object_list)

    @staticmethod
    def get_default_position():
        """Get the default position in the scene.

        Returns:
            tuple: The default position in the scene as (x, y).
        """
        return environment.width // 2, environment.height // 2

    def get_object_mask(self, obj):
        """Get a list of objects that could block the given object.

        Args:
            obj: The object to check for blocking.

        Returns:
            list: The list of objects that could be blocking the given object.
        """
        blocking_object_list = []
        if obj not in self.preliminary_display_order:
            return blocking_object_list

        object_index = self.preliminary_display_order.index(obj)

        for masking_object_index, masking_object in enumerate(self.preliminary_display_order):
            if should_not_block_clicks(obj, object_index, masking_object, masking_object_index):
                continue
            if obj.get_rect().colliderect(masking_object.get_rect()):
                blocking_object_list.append(masking_object)

        return blocking_object_list

    def clear(self):
        """Clear all objects from the scene."""
        self.objects = []
        self.processing_order = []
        self.display_order = []

    def schedule_processing(self):
        """Schedule the processing order of objects."""
        self.processing_order = []

        self.get_objects().sort(key=lambda x: x.z)

        for obj in self.objects:
            items_to_be_processed = obj.schedule_processing()
            self.processing_order.extend(items_to_be_processed)
        self.processing_order.sort(key=lambda x: x.z)

    def process_object(self, obj):
        """Process a specific object.

        Args:
            obj: The object to process.
        """
        cant_be_processed = not hasattr(obj, "process") or obj not in self.processing_order
        obj_destroyed = hasattr(obj, "destroyed") and obj.destroyed
        if cant_be_processed or obj_destroyed:
            return

        obj.process()

    def process(self):
        """Process and display objects in the scene."""
        environment.get_screen().fill(self.background_color)
        self.preliminary_display_order = []
        self.schedule_processing()

        # Generate preliminary display_order
        for obj in self.objects:
            if hasattr(obj, "get_displayable_objects"):
                self.preliminary_display_order.extend(obj.get_displayable_objects())
        self.preliminary_display_order.sort(key=lambda x: x.z)

        # Process objects.
        for obj in reversed(self.processing_order.copy()):
            self.process_object(obj)

        # Generate display order
        self.display_order = []
        for obj in self.objects:
            if hasattr(obj, "get_displayable_objects"):
                self.display_order.extend(obj.get_displayable_objects())
        self.display_order.sort(key=lambda x: x.z)

        # Display objects.
        for obj in self.display_order:
            if hasattr(obj, "get_display_surface") and callable(obj.get_display_surface):
                surface, rect = obj.get_display_surface()
                environment.get_screen().blit(surface, rect)

        # Remove destroyed objects
        for obj in self.objects:
            if hasattr(obj, "destroyed") and obj.destroyed:
                self.objects.remove(obj)

    def create_scene(self, *args, **kwargs):
        """Virtual method for creating a scene. Implemented by child scene classes."""
        pass

    def create_object(self, object_class, *args, **kwargs):
        """Create a new object and adds it to the scene.

         Args:
             object_class (callable): The class of the object to be created.
         """
        new_object = object_class(*args, **kwargs)
        self.add_object(new_object)


def get_tick_manager():
    """Returns the current tick manager.

    Returns:
        TickManager or None: The tick manager of the current game state.
    """
    return game_state.tick_manager


def find_all_ancestors(current_object):
    """Finds all ancestors of an object and returns it.

    Args:
        current_object: The object which ancestors should be returned.

    Returns:
        All non-None ancestors of current_object.
    """
    ancestors = []
    while hasattr(current_object, "parent") and current_object is not None:
        ancestors.append(current_object)
        current_object = current_object.parent
    return ancestors


def calculate_hierarchy_depth_difference(obj1, obj2):
    """Calculates the distance between two objects in their hierarchy tree.

    Args:
        obj1: The first object.
        obj2: The second object.

    Returns:
        int or None: The difference between the two objects' hierarchy depth if they share the same root;
        otherwise, returns None. If the difference is positive, the first object is higher up in the hierarchy
        than the second object.
    """

    ancestors_of_obj1 = find_all_ancestors(obj1)
    ancestors_of_obj2 = find_all_ancestors(obj2)
    for ancestor in ancestors_of_obj2:
        if ancestor in ancestors_of_obj1:
            return ancestors_of_obj1.index(ancestor) - ancestors_of_obj2.index(ancestor)

    return None


def should_not_block_clicks(obj, object_index, masking_object, masking_object_index):
    """Determines whether an object should block the clicks of another object or not.

    Args:
        obj: The object for which the click-blocking status is determined.
        masking_object: The object that might block clicks.
        object_index (int): The index of obj in the processing order.
        masking_object_index (int): The index of masking_object in the processing order.

    Returns:
        bool: True if the clicks of the first object should be blocked by the second object, False otherwise.
    """
    same_object = masking_object == obj
    not_opaque = hasattr(masking_object, "opaque") and not masking_object.opaque
    has_rect = hasattr(masking_object, "get_rect")
    is_below = masking_object.z < obj.z
    is_destroyed = hasattr(masking_object, "destroyed") and masking_object.destroyed
    if same_object or not_opaque or not has_rect or is_below or is_destroyed:
        return True
    same_z = masking_object.z == obj.z

    relation_distance = calculate_hierarchy_depth_difference(masking_object, obj)

    visually_blocked = object_index < masking_object_index
    if relation_distance is None:
        dont_block_clicks = same_z and not visually_blocked
    else:
        related_up = relation_distance > 0
        related_down = relation_distance < 0
        siblings = relation_distance == 0
        non_opaque_to_ancestor = related_up and not masking_object.opaque_to_ancestor
        non_opaque_to_descendant = related_down and not masking_object.opaque_to_descendant
        non_opaque_to_sibling = siblings and not masking_object.opaque_to_sibling
        non_opaque_to_relative = non_opaque_to_ancestor or non_opaque_to_descendant or non_opaque_to_sibling
        dont_block_clicks = same_z and (non_opaque_to_relative or not visually_blocked)

    return dont_block_clicks


def get_scene_manager():
    """Returns the surface manager associated with the current game state.

    Returns:
        SceneManager or None: The surface manager of the current game state.
    """
    return game_state.scene_manager


def set_scene_manager(scene_manager):
    """Sets the scene manager for the game state.

    Args:
        scene_manager (SceneManager or None): The surface manager to be set.
    """
    game_state.scene_manager = scene_manager


def get_surface_manager():
    """Returns the surface manager associated with the current game state.

    Returns:
        SurfaceManager or None: The surface manager of the current game state.
    """
    return game_state.surface_manager


def schedule_start_of_tick_function(function, arguments):
    """Schedules a function to be executed at the start of the next game tick.

    Args:
        function (callable): The function to be executed.
        arguments (list): The list of arguments to be passed to the function.
    """
    game_state.tick_manager.start_of_tick_functions.append(function)
    game_state.tick_manager.start_of_tick_arguments.append(arguments)


def schedule_end_of_tick_function(function, arguments):
    """Schedules a function to be executed at the end of the current game tick.

    Args:
        function (callable): The function to be executed.
        arguments (list): The list of arguments to be passed to the function.
    """
    game_state.tick_manager.end_of_tick_functions.append(function)
    game_state.tick_manager.end_of_tick_arguments.append(arguments)


def start_tick():
    """Executes start-of-tick functions."""
    utils.execute_multiple_functions(game_state.tick_manager.start_of_tick_functions,
                                     game_state.tick_manager.start_of_tick_arguments)
    game_state.tick_manager.start_of_tick_functions = []
    game_state.tick_manager.start_of_tick_arguments = []


def end_tick():
    """Executes end-of-tick functions and resets environment events."""
    utils.execute_multiple_functions(game_state.tick_manager.end_of_tick_functions,
                                     game_state.tick_manager.end_of_tick_arguments)
    game_state.tick_manager.end_of_tick_functions = []
    game_state.tick_manager.end_of_tick_arguments = []

    environment.set_events_last_tick(environment.events_this_tick)
    environment.set_events_this_tick({"left_mouse_button": False, "right_mouse_button": False, "pressed_keys": []})


def schedule_scene_change(scene):
    """Schedules a scene change with the scene manager.

    Args:
        scene (Scene): The scene that the scene manager will set to the current scene.
    """
    get_scene_manager().schedule_scene_change(scene)


def save_state(save_number=0):
    """Schedules the asynchronous saving of the game state at the end of the current tick.

    Args:
        save_number (int): The identifier for the save_state file. Defaults to 0.
    """
    schedule_end_of_tick_function(_save_state, [save_number])


def _save_state(save_number):
    """Saves the game state to a file. Should be called at the end of the tick.

    Args:
        save_number (int): The identifier for the save_state file.
    """
    with open(f'save_{save_number}.txt', 'wb') as save_file:
        savable_game_state = game_state.get_savable_copy()
        pickle.dump(savable_game_state, save_file)


def load_state(save_number=0):
    """Schedules the asynchronous loading of the game state at the end of the current tick.

    Args:
        save_number (int): The identifier of the save_state file. Defaults to 0.
    """
    schedule_end_of_tick_function(_load_state, [save_number])


def _load_state(save_number):
    """Load a saved game state from a file.

    Args:
        save_number (int): The identifier of the save_state file.

    Notes:
        This function loads the game state from the specified save_state file, including surface manager data and the
        scene manager. It updates the current game state accordingly.
    """
    with open(f'save_state{save_number}.txt', 'rb') as save_file:
        loaded_game_state = pickle.load(save_file)
        get_surface_manager().load_surfaces(loaded_game_state)
        set_scene_manager(loaded_game_state.scene_manager)
        game_state.load_from_surface_manager()


def process_current_scene():
    """Process the current scene."""
    get_scene_manager().get_current_scene().process()


def get_fps():
    """Gets the current FPS of the application.

    Returns:
        str: A string representing the current fps, up to one decimal.
    """
    fps = environment.clock.get_fps()
    return str(round(float(fps), 1))


def start_text_input():
    """Starts input event listening"""
    pygame.key.start_text_input()


def stop_text_input():
    """Stops input event listening"""
    pygame.key.stop_text_input()


game_state = GameState()
environment = Environment()
