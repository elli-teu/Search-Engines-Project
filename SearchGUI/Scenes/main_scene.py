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
        self.selected_query_type = search.QueryType.intersection_query
        self.search_results = []
        self.start_index = 0

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

        union_button = assets.Button(search_box.x,
                                     y=30, height=0, resize_to_fit_text=True, text="Union Search", font_size=20,
                                     left_click_function=set_query_type, left_click_args=[search.QueryType.union_query],
                                     name="union_button")
        intersection_button = assets.Button(union_button.x + union_button.width + standard_space,
                                            y=30, height=0, resize_to_fit_text=True, text="Intersection Search",
                                            font_size=20,
                                            left_click_function=set_query_type,
                                            left_click_args=[search.QueryType.intersection_query],
                                            name="intersection_button", color=BLUE)
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
                                         left_click_function=update_result_buttons_relative, left_click_args=[-1])
        scroll_down_button = assets.Button(x=environment.get_width() / 2 + 400 + standard_space, y=800, width=40,
                                           height=40,
                                           source_image_id=file_op.load_image(image_location + "down_arrow.png"),
                                           left_click_function=update_result_buttons_relative, left_click_args=[1])

        self.add_object(number_box)

        objects = [search_box, search_button,
                   union_button, intersection_button, phrase_button,
                   scroll_up_button, scroll_down_button]
        self.add_multiple_objects(objects)

        return self


def set_query_type(query_type):
    union_button = utils.find_object_from_name(game_engine.get_scene_manager().get_current_scene().get_objects(),
                                               "union_button")
    intersection_button = utils.find_object_from_name(game_engine.get_scene_manager().get_current_scene().get_objects(),
                                                      "intersection_button")
    phrase_button = utils.find_object_from_name(game_engine.get_scene_manager().get_current_scene().get_objects(),
                                                "phrase_button")
    buttons = [union_button, intersection_button, phrase_button]
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
    result_buttons = []
    scene = game_engine.get_scene_manager().get_current_scene()
    for obj in scene.get_objects():
        if obj.name is not None and "result" in obj.name and "_button" in obj.name and not obj.destroyed:
            result_buttons.append(obj)

    if start_index + len(result_buttons) > len(scene.search_results):
        start_index = len(scene.search_results) - len(result_buttons)
    if start_index < 0:
        start_index = 0
    scene.start_index = start_index

    for i, button in enumerate(result_buttons):
        button_text = scene.search_results[start_index + i].lstrip(" ")
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
    create_result_buttons(results)

    update_result_buttons(0)
    number_box = utils.find_object_from_name(current_scene.get_objects(), "number_box")
    number_box.set_text(f"Number of results: {number_of_results}")


def clear_old_buttons():
    current_scene = game_engine.get_scene_manager().get_current_scene()
    for obj in current_scene.get_objects():
        if obj.name is not None and "result" in obj.name and "_button" in obj.name:
            obj.destroy()


def create_result_buttons(results):
    current_scene = game_engine.get_scene_manager().get_current_scene()
    number_of_shown_results = 10
    start_height = 250
    y = start_height
    for i, result in enumerate(results[:number_of_shown_results]):
        result_button = assets.Button(x=environment.get_width() / 2 - 400, y=y, width=800, height=50, color=LIGHT_GREY,
                                      font_size=15,
                                      text_centering=(assets.CenteringOptions.LEFT, assets.CenteringOptions.CENTER),
                                      text_wrap=True, name=f"result{i}_button", include_border=True,
                                      left_click_function=create_result_overlay, left_click_args=[i])
        y += result_button.height + standard_space
        current_scene.add_object(result_button)


def create_result_overlay(button_index):
    current_scene = game_engine.get_scene_manager().get_current_scene()
    result_overlay = assets.Overlay(x=environment.get_width()/2 - 200, z=1, width=400, height=400)
    result_text_box = result_overlay.get_box()
    result_text_box.font_size = 20
    result_text_box.text_wrap = True
    result_text_box.text_centering = (assets.CenteringOptions.LEFT, assets.CenteringOptions.CENTER)
    result_text_box.set_text(current_scene.search_results[current_scene.start_index + button_index].lstrip(" "))
    current_scene.add_object(result_overlay)
