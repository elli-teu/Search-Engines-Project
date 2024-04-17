from game_engine import environment, Scene
import game_engine as game_engine
from constants import *
import assets as assets
import Scenes.scenes as scenes
import search
import utility_functions as utils
import file_operations as file_op


class MainScene(Scene):
    """Creates a scene used displaying the main menu.

    Inherits all attributes from the Scene class, and implements the create_scene method.
    """

    def __init__(self):
        super().__init__(name=scenes.MAIN_SCENE)
        self.selected_query_type = search.QueryType.smart_query
        self.search_results = []
        self.start_index = 0
        self.result_buttons = []

    def create_scene(self):
        """Creates the main menu scene.

        Returns:
            Scene: The main menu scene containing buttons for starting, loading, testing, and exiting the game.
        """
        self.background_color = WHITE
        font_size = 20
        search_box = assets.InputField(x=environment.get_width() / 2 - (500 + 110) / 2, y=110,
                                       height=30, width=500)
        search_box.return_key_function = search_from_box
        search_box.return_key_args = [search_box]

        search_button = assets.Button(search_box.x + search_box.width + standard_space,
                                      y=110, height=0, width=110, resize_to_fit_text=True, text="Search",
                                      font_size=font_size,
                                      left_click_function=search_from_box, left_click_args=[search_box],
                                      name="search_button")
        smart_search_button = assets.Button(search_box.x,
                                            y=30, height=0, resize_to_fit_text=True, text="Smart Search", font_size=20,
                                            left_click_function=set_query_type,
                                            left_click_args=[search.QueryType.smart_query],
                                            name="smart_button", color=BLUE)

        union_button = assets.Button(search_box.x + smart_search_button.width + standard_space,
                                     y=30, height=0, resize_to_fit_text=True, text="Union Search", font_size=20,
                                     left_click_function=set_query_type, left_click_args=[search.QueryType.union_query],
                                     name="union_button")
        intersection_button = assets.Button(union_button.x + union_button.width + standard_space,
                                            y=30, height=0, resize_to_fit_text=True, text="Intersection Search",
                                            font_size=20,
                                            left_click_function=set_query_type,
                                            left_click_args=[search.QueryType.intersection_query],
                                            name="intersection_button")

        phrase_button = assets.Button(intersection_button.x + intersection_button.width + standard_space,
                                      y=30, height=0, resize_to_fit_text=True, text="Phrase Search", font_size=20,
                                      left_click_function=set_query_type,
                                      left_click_args=[search.QueryType.phrase_query],
                                      name="phrase_button")

        number_box = assets.Box(x=environment.get_width() / 2 - 194 / 2, y=150, height=30, width=194, color=GREY,
                                text=f"Number of results:", font_size=15, text_offset=5,
                                text_centering=(assets.CenteringOptions.LEFT, assets.CenteringOptions.CENTER),
                                name="number_box", include_border=True)

        scroll_up_button = assets.Button(x=environment.get_width() / 2 + 400 + standard_space, y=250, width=40,
                                         height=40,
                                         source_image_id=file_op.load_image(image_location + "up_arrow.png"),
                                         left_click_function=update_result_buttons_relative, left_click_args=[-1],
                                         name="scroll_up_button")
        scroll_down_button = assets.Button(x=environment.get_width() / 2 + 400 + standard_space, y=800, width=40,
                                           height=40,
                                           source_image_id=file_op.load_image(image_location + "down_arrow.png"),
                                           left_click_function=update_result_buttons_relative, left_click_args=[1],
                                           name="scroll_down_button")
        scroll_button_y = 290
        scroll_button_height = scroll_down_button.y - scroll_up_button.y - scroll_up_button.height
        scroll_button = ScrollButton(x=environment.get_width() / 2 + 400 + standard_space,
                                     y=scroll_button_y,
                                     width=40, height=scroll_button_height,
                                     name="scroll_button", fixed_axis="vertical", start_value=scroll_button_y,
                                     stop_value=scroll_down_button.y)

        self.add_object(number_box)

        objects = [search_box, search_button,
                   smart_search_button, union_button, intersection_button, phrase_button,
                   scroll_up_button, scroll_down_button, scroll_button]
        self.add_multiple_objects(objects)

        return self


def set_query_type(query_type):
    query_types = [search.QueryType.smart_query, search.QueryType.union_query, search.QueryType.intersection_query,
                   search.QueryType.phrase_query]

    buttons = [x for x in game_engine.get_scene_manager().get_current_scene().get_objects() if x.name is not None
               and x.name.split("_")[0] in query_types]

    for button in buttons:
        if query_type in button.name:
            button.set_color(BLUE)
        else:
            button.set_color(GREY)
    game_engine.get_scene_manager().get_current_scene().selected_query_type = query_type


def update_result_buttons_relative(change_in_index):
    scene = game_engine.get_scene_manager().get_current_scene()
    update_result_buttons(scene.start_index + change_in_index)


def update_result_buttons(start_index):
    scene = game_engine.get_scene_manager().get_current_scene()

    if start_index + len(scene.result_buttons) > len(scene.search_results):
        start_index = len(scene.search_results) - len(scene.result_buttons)
    if start_index < 0:
        start_index = 0
    scene.start_index = start_index
    for i, button in enumerate(scene.result_buttons):
        button_text = scene.search_results[start_index + i]["transcript"].lstrip(" ")
        button_text = " ".join(button_text.split(" ")[:10]) + "... - [Click to show more]"
        button.set_text(button_text)


def search_from_box(input_box):
    current_scene = game_engine.get_scene_manager().get_current_scene()
    clear_old_buttons()

    query_type = game_engine.get_scene_manager().get_current_scene().selected_query_type
    text = input_box.text
    query = search.generate_query(text, query_type)
    response = search.execute_query(query, n=1000)
    number_of_results = search.get_number_of_hits(response)
    if number_of_results == 10000:
        number_of_results = str(number_of_results) + "+"
    else:
        number_of_results = str(number_of_results)

    results = search.get_first_n_results(response, n=1000)
    current_scene.search_results = results
    create_result_buttons(len(results))
    scroll_button = utils.find_object_from_name(current_scene.get_objects(), "scroll_button")
    scroll_up_button = utils.find_object_from_name(current_scene.get_objects(), "scroll_up_button")
    scroll_down_button = utils.find_object_from_name(current_scene.get_objects(), "scroll_down_button")
    max_height = scroll_down_button.y - scroll_up_button.y - scroll_up_button.height
    if len(results) == 0:
        scroll_button_height = max_height
    else:
        scroll_button_height = max(max_height * len(current_scene.result_buttons) / len(results), 20)
    scroll_button.set_height(scroll_button_height)
    scroll_button.set_y(scroll_up_button.y + scroll_up_button.height)

    update_result_buttons(0)
    number_box = utils.find_object_from_name(current_scene.get_objects(), "number_box")
    number_box.set_text(f"Number of results: {number_of_results}")


def clear_old_buttons():
    current_scene = game_engine.get_scene_manager().get_current_scene()
    for obj in current_scene.get_objects():
        if obj.name is not None and "result" in obj.name and "_button" in obj.name:
            obj.destroy()
    current_scene.result_buttons = []


def create_result_buttons(number_of_results):
    current_scene = game_engine.get_scene_manager().get_current_scene()
    number_of_shown_results = min(10, number_of_results)
    start_height = 250
    y = start_height
    result_buttons = []
    for i in range(number_of_shown_results):
        result_button = assets.Button(x=environment.get_width() / 2 - 400, y=y, width=800, height=50, color=LIGHT_GREY,
                                      font_size=15,
                                      text_centering=(assets.CenteringOptions.LEFT, assets.CenteringOptions.CENTER),
                                      text_wrap=True, name=f"result{i}_button", include_border=True,
                                      left_click_function=create_result_overlay, left_click_args=[i])
        y += result_button.height + standard_space
        current_scene.add_object(result_button)
        result_buttons.append(result_button)

    current_scene.result_buttons = result_buttons


def create_result_overlay(button_index):
    current_scene = game_engine.get_scene_manager().get_current_scene()
    relevant_result = current_scene.search_results[current_scene.start_index + button_index]
    podcast_title = "Podcast title"  # relevant_result["podcast_title"]
    episode_title = "Episode title"  # relevant_result["episode_title"]
    author = "Author"  # relevant_result["author"]
    podcast_image = file_op.load_image(image_location+"placeholder.jpg")
    transcript = relevant_result["transcript"].lstrip(" ")

    result_overlay = assets.Overlay(x=standard_space, z=1, width=450, height=800)
    result_overlay.external_process_function = utils.destroy_on_external_clicks
    result_overlay.external_process_arguments = [result_overlay, [result_overlay.get_rect()]]

    podcast_title_box = assets.Box(x=result_overlay.x + standard_space, y=result_overlay.y + standard_space, z=1,
                                   width=result_overlay.width - 2 * standard_space, height=0, resize_to_fit_text=True,
                                   font_size=40,
                                   text=podcast_title, text_offset=0)
    result_overlay.add_child(podcast_title_box)

    episode_title_box = assets.Box(x=result_overlay.x + standard_space,
                                   y=podcast_title_box.y + podcast_title_box.height + standard_space, z=1,
                                   width=result_overlay.width - 2 * standard_space, height=0, resize_to_fit_text=True,
                                   font_size=27,
                                   text=episode_title, text_offset=0)
    result_overlay.add_child(episode_title_box)

    snippet_author_box = assets.Box(x=result_overlay.x + standard_space,
                                    y=episode_title_box.y + episode_title_box.height + standard_space, z=1,
                                    width=result_overlay.width - 2 * standard_space, height=0, resize_to_fit_text=True,
                                    font_size=22,
                                    text=author, text_offset=0)
    result_overlay.add_child(snippet_author_box)
    image_width = 192
    image_height = 108
    podcast_image_box = assets.Box(x=result_overlay.x + result_overlay.width/2 - image_width / 2,
                                   y=snippet_author_box.y + snippet_author_box.height + standard_space, z=1,
                                   width=image_width, height=image_height,
                                   source_image_id=podcast_image)
    result_overlay.add_child(podcast_image_box)

    result_text_box = assets.Box(x=result_overlay.x + standard_space,
                                 y=result_overlay.y + result_overlay.height / 2 + standard_space, z=1,
                                 width=result_overlay.width - 2 * standard_space,
                                 height=result_overlay.height / 2 - 2 * standard_space, font_size=20,
                                 text_wrap=True,
                                 text_centering=(assets.CenteringOptions.LEFT, assets.CenteringOptions.CENTER),
                                 text=transcript,
                                 include_border=True)
    result_overlay.add_child(result_text_box)
    current_scene.add_object(result_overlay)


class ScrollButton(assets.MobileButton):
    """
    A class for a scroll button that can be moved using the mouse.
    Attributes:

        fixed_axis (string): Along what axis the button's position should be fixed
        start_value (float): The smaller endpoint of where the button should stop
        stop_value (float): The larger endpoint.
    """

    def __init__(self, x=0, y=0, z=1, width=200, height=120, color=(100, 100, 100), indicator_color=WHITE,
                 indicate_hover=False,
                 indicate_clicks=False, alpha=255, static=False,
                 source_image_id=None, text="", font_size=40,
                 text_color=BLACK, text_centering=(assets.CenteringOptions.CENTER, assets.CenteringOptions.CENTER),
                 x_centering=assets.CenteringOptions.LEFT,
                 y_centering=assets.CenteringOptions.TOP,
                 include_border=False, name=None, parent=None,
                 left_trigger_keys=None, left_hold_function=None,
                 left_hold_args=None, right_trigger_keys=None,
                 right_click_function=None, right_click_args=None, right_hold_function=None, right_hold_args=None,
                 key_functions=None, external_process_function=None, external_process_arguments=None,
                 fixed_axis="vertical", start_value=0, stop_value=120):
        """Creates a new scroll button.

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
            fixed_axis (string): Along what axis the button's position should be fixed
            start_value (float): The smaller endpoint of where the button should stop
            stop_value (float): The larger endpoint.
        """
        super().__init__(x=x, y=y, z=z, width=width, height=height, color=color, indicator_color=indicator_color,
                         indicate_hover=indicate_hover, indicate_clicks=indicate_clicks, alpha=alpha,
                         source_image_id=source_image_id,
                         text=text, font_size=font_size, text_color=text_color, text_centering=text_centering,
                         x_centering=x_centering, y_centering=y_centering,
                         include_border=include_border,
                         name=name, parent=parent, static=static,
                         left_trigger_keys=left_trigger_keys, right_trigger_keys=right_trigger_keys,
                         left_hold_function=left_hold_function,
                         left_hold_args=left_hold_args,
                         right_click_function=right_click_function, right_click_args=right_click_args,
                         right_hold_function=right_hold_function, right_hold_args=right_hold_args,
                         key_functions=key_functions, external_process_function=external_process_function,
                         external_process_arguments=external_process_arguments)
        self.fixed_axis = fixed_axis
        self.start_value = start_value
        self.stop_value = stop_value

    def move(self):
        """Handles the movement of the mobile button."""
        if not self.moving:
            return
        mouse_position = environment.get_mouse_position()
        if self.fixed_axis == "vertical":
            scroll_length = mouse_position[1] - self.click_y
            scroll_length = utils.clamp(scroll_length, self.start_value, self.stop_value - self.height)
            self.set_y(scroll_length)
        elif self.fixed_axis == "horizontal":
            scroll_length = mouse_position[0] - self.click_x
            scroll_length = utils.clamp(scroll_length, self.start_value, self.stop_value - self.width)
            self.set_x(scroll_length)
        else:
            raise ValueError(f"{self.fixed_axis} is not a valid axis.")

        total_scroll_length = (self.stop_value - self.start_value - self.height)
        if total_scroll_length == 0:
            fraction_scrolled = 0
        else:
            fraction_scrolled = (scroll_length - self.start_value) / total_scroll_length

        current_scene = game_engine.get_scene_manager().get_current_scene()
        search_results = current_scene.search_results
        update_result_buttons(int(fraction_scrolled * (len(search_results) - len(current_scene.result_buttons))))

    def update_click_position(self):
        """Updates the click position of the MobileButton."""
        mouse_position = environment.get_mouse_position()
        if not self.moving or self.position_inside_bounds(mouse_position):
            self.click_x, self.click_y = mouse_position[0] - self.x, mouse_position[1] - self.y

    def position_inside_bounds(self, position):
        if self.fixed_axis == "vertical":
            value = position[1]
        elif self.fixed_axis == "horizontal":
            value = position[0]
        else:
            raise ValueError(f"{self.fixed_axis} is not a valid axis.")

        if self.start_value <= value <= self.stop_value:
            return True
        return False
