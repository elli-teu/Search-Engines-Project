import game_engine
import sys


def common_elements(list1, list2):
    """Checks if two lists have any elements in common.

    Args:
        list1 (list): The first list.
        list2 (list): The second list.

    Returns:
        bool: True if list1 and list2 have elements in common, False otherwise.
    """
    for element in list1:
        if element in list2:
            return True
    return False


def eprint(*args, **kwargs):
    """Prints to stderr."""
    print(*args, file=sys.stderr, **kwargs)


def clamp(x, lower, upper):
    """Clamps a value 'x' to the range ['lower', 'upper'].

     Args:
         x: The value to be clamped.
         lower: The lower bound of the range.
         upper: The upper bound of the range.

     Returns:
         The clamped value within the specified range.
     """
    if x < lower:
        return lower
    elif x > upper:
        return upper
    return x


def execute_multiple_functions(functions, argument_list):
    """Executes multiple functions with corresponding argument lists.

    Args:
        functions (list): List of functions to be executed.
        argument_list (list): List of argument lists corresponding to the functions.
    """
    for i, function in enumerate(functions):
        if isinstance(argument_list[i], dict):
            function(**argument_list[i])
        else:
            function(*argument_list[i])


def find_object_from_name(obj_list, name):
    """Finds an object with a specific name in a list.

    Args:
        obj_list (list): The list of objects to search.
        name (str): The name of the object to find.

    Returns:
        The first object with the specified name, or None if not found.
    """
    for obj in obj_list:
        if hasattr(obj, "name") and obj.name == name:
            return obj
    return None


def find_objects_from_type(obj_list, match_type):
    """Finds objects of a specific type in a list.

    Args:
        obj_list (list): The list of objects to search.
        match_type (type): The type of objects to find.

    Returns:
        list: List of objects with the specified type found in the list.
    """
    found_objects = []
    for obj in obj_list:
        if hasattr(obj, "name") and isinstance(obj, match_type):
            found_objects.append(obj)
    return found_objects


def detect_external_clicks(allowed_rect_list):
    """Detects if the mouse button (right or left) has been clicked while not on top of the allowed rects.

    Args:
        allowed_rect_list (list): The list containing the allowed rects.

    Returns:
        bool: True if an external click was detected, False otherwise.
    """
    mouse_click_this_tick = game_engine.environment.get_left_mouse_click_this_tick() or game_engine.environment.\
        get_right_mouse_click_this_tick()

    mouse_click_last_tick = game_engine.environment.get_left_mouse_click_last_tick() or game_engine.environment.\
        get_right_mouse_click_last_tick()
    if not mouse_click_this_tick or (mouse_click_this_tick and mouse_click_last_tick):
        return False

    mouse_position = game_engine.environment.get_mouse_position()
    for rect in allowed_rect_list:
        if rect.collidepoint(mouse_position):
            return False
    return True


def destroy_on_external_clicks(obj, allowed_rect_list):
    """Destroys an object if a mouse click occurs outside a list of allowed rectangles.

    Args:
        obj: The object to be destroyed.
        allowed_rect_list (list): List of pygame.Rect objects representing allowed areas.
    """
    if not detect_external_clicks(allowed_rect_list):
        return
    obj.destroy()


def center_rectangle(low, high, width):
    """Calculates the coordinate so that a rectangle with a certain width has it's it middle between two points.

    Args:
        low (float): The coordinate of the lower point.
        high (float): The coordinate of the higher point.
        width (float): The width of the rectangle.

    Returns:
        float: The coordinate that ensures the rectangle is centered.
    """
    midpoint = calculate_midpoint(low, high)
    return round(low + midpoint - width / 2)


def calculate_midpoint(low, high):
    """Calculates the midpoint of an interval that starts at low and stops at high.

    Args:
        low (float): The minimum of the interval.
        high (float): The maximum of the interval.

    Returns:
        The midpoint of low and high.
    """
    return (high - low) / 2
