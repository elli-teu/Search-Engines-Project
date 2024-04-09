from game_engine import environment, Scene
import game_engine as game_engine
from constants import *
import sys
import assets as assets
import Scenes.scenes as scenes
import search
import utility_functions as utils


class MainScene(Scene):
    """Creates a scene used displaying the main menu.

    Inherits all attributes from the Scene class, and implements the create_scene method.
    """

    def __init__(self):
        super().__init__(name=scenes.MAIN_SCENE)
        self.selected_query_type = search.QueryType.intersection_query

    def create_scene(self):
        """Creates the main menu scene.

        Returns:
            Scene: The main menu scene containing buttons for starting, loading, testing, and exiting the game.
        """
        self.background_color = WHITE
        font_size = 20
        search_box = assets.InputField(x=environment.get_width() / 2 - (500 + 110) / 2, y=110,
                                       height=30, width=500)
        search_button = assets.Button(search_box.x + search_box.width + standard_space,
                                      y=110, height=0, width=110, resize_to_fit_text=True, text="Search", font_size=font_size,
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

        self.add_object(number_box)


        objects = [search_box, search_button, union_button, intersection_button, phrase_button]
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


def search_from_box(input_box):
    current_scene = game_engine.get_scene_manager().get_current_scene()
    for obj in current_scene.get_objects():
        if obj.name and "result" in obj.name:
            obj.destroy()

    query_type = game_engine.get_scene_manager().get_current_scene().selected_query_type
    text = input_box.text
    query = search.generate_query(text, query_type)
    response = search.execute_query(query)
    number_of_results = search.get_number_of_hits(response)
    if number_of_results == 10000:
        number_of_results = str(number_of_results) + "+"
    else:
        number_of_results = str(number_of_results)
    results = search.get_first_n_results(response, n=10)

    start_height = 250
    y = start_height
    for i, result in enumerate(results):
        result_box = assets.Box(x=environment.get_width() / 2 - 400, y=y, width=800, color=LIGHT_GREY, text=result, font_size=15,
                                text_centering=(assets.CenteringOptions.LEFT, assets.CenteringOptions.TOP),
                                text_wrap=True, name=f"result{i}_box", include_border=True)
        result_box.set_height(2 * result_box.text_offset + result_box.get_text_height())
        y += result_box.height + standard_space
        current_scene.add_object(result_box)
    number_box = utils.find_object_from_name(current_scene.get_objects(), "number_box")
    number_box.set_text(f"Number of results: {number_of_results}")


