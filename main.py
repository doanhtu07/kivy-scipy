# import pandas as pd
import csv
import io
import os
from functools import partial

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Mesh
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from BufferTable import BufferTableScreen
from GenBCScreen import GenBCScreen
from TitrationScreen import TitrationScreen

# Load the kv file for the GUI layout
Builder.load_file("main.kv")


# Define HomeScreen class inheriting from Screen
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.parameters = {}  # Initialize parameters dictionary
        self.last_dir = ""  # Initialize last directory string
        self.start_new = False  # Initialize start_new flag
        self.conTitr = 0  # Initialize conTitr value

    # Receive data method
    def receive_data(self, start_new):
        self.start_new = start_new  # Update start_new flag
        if self.start_new:
            self.clear_data()  # Clear data if starting new

    # Clear data method
    def clear_data(self):
        self.clear_text_inputs(self)  # Clear all input boxes
        self.last_dir = ""  # Reset last directory
        self.parameters = {}  # Reset parameters dictionary

    # Recursive method to clear text inputs
    def clear_text_inputs(self, widget):
        for child in widget.children:
            if isinstance(child, TextInput):
                child.text = ""  # Clear text if child is TextInput
            else:
                self.clear_text_inputs(
                    child
                )  # Recursive call for non-TextInput children

    # Update parameter method
    def update_parameter(self, instance, value):
        self.parameters[instance.id] = value  # Update parameter dictionary

    # Show file chooser method
    def show_file_chooser(self):
        content = BoxLayout(orientation="vertical")  # Create vertical BoxLayout
        filechooser = FileChooserListView()  # Create FileChooserListView
        content.add_widget(filechooser)  # Add FileChooserListView to content
        btn = Button(text="Select", size_hint_y=None, height=40)  # Create Select button
        btn.bind(
            on_press=lambda x: self.load_file(filechooser.selection)
        )  # Bind button press to load_file method
        content.add_widget(btn)  # Add button to content

        self.popup = Popup(
            title="File Chooser", content=content, size_hint=(0.9, 0.9)
        )  # Create and open popup
        self.popup.open()

    # Load file method
    def load_file(self, selection):
        if selection:
            file_path = selection[0]  # Get selected file path
            self.last_dir = os.path.dirname(file_path)  # Save the directory path
            self.process_file_data(file_path)  # Process file data
        self.popup.dismiss()  # Dismiss popup

    # Process file data method
    def process_file_data(self, file_path):
        try:
            with open(file_path, "r") as csvfile:
                reader = csv.reader(io.StringIO(csvfile.read()))  # Read CSV file
                new_parameters = reader.set_index("Parameter").to_dict()[
                    "Value"
                ]  # Convert to dictionary

                self.parameters = new_parameters  # Update parameters dictionary
                self.update_inputs(new_parameters)  # Update inputs with new parameters

        except Exception as e:
            self.show_popup(
                "Error", f"An error occurred while processing the file data: {str(e)}"
            )  # Show error popup

    # Update inputs method
    def update_inputs(self, parameters):
        # Update the text inputs with the file's values
        self.ids.ingredient.text = parameters.get("ingredient", "")
        self.ids.concentration_titration.text = str("")
        self.ids.acid_concentration.text = str(parameters.get("HCl", ""))
        self.ids.base_concentration.text = str(parameters.get("NaOH", ""))
        self.ids.vol_titrated.text = str(parameters.get("Init_Vol", ""))
        self.ids.nacl.text = str(parameters.get("NaClpercent", ""))

        # Update the inputs if user changes the values
        self.ids.ingredient.bind(text=partial(self.update_parameters, "ingredient"))
        self.ids.concentration_titration.bind(text=self.update_concentration_titration)
        self.ids.acid_concentration.bind(text=partial(self.update_parameters, "HCl"))
        self.ids.base_concentration.bind(text=partial(self.update_parameters, "NaOH"))
        self.ids.vol_titrated.bind(text=partial(self.update_parameters, "Init_Vol"))
        self.ids.nacl.bind(text=partial(self.update_parameters, "NaClpercent"))

    # Update parameters method
    def update_parameters(self, key, instance, value):
        self.parameters[key] = value

    # Update concentration titration method
    def update_concentration_titration(self, instance, value):
        self.conTitr = value

    # Go to titration graph method
    def go_to_titration_graph(self):
        self.collected_data = {
            "ingredient": self.ids.ingredient.text,
            "nacl": self.parameters.get("NaClpercent", ""),
            "init_vol": self.parameters.get("Init_Vol", ""),
            "molHCl": self.parameters.get("HCl", ""),
            "molNaOH": self.parameters.get("NaOH", ""),
            "mingap": self.parameters.get("MinGap", ""),
            "increment": self.parameters.get("Increment", ""),
            "removeVal": self.parameters.get("pH", ""),
            "order": self.parameters.get("Order", ""),
            "minConc": self.parameters.get("MinConc", ""),
            "npKs": self.parameters.get("NpKs", ""),
            "uB": self.parameters.get("UB", ""),
            "lB": self.parameters.get("LB", ""),
            "pK_tol": self.parameters.get("pK_tol", ""),
            "trim_beg": self.parameters.get("Trim_beg", ""),
            "trim_end": self.parameters.get("Trim_end", ""),
        }  # Collect data
        self.manager.get_screen("titration_screen").receive_data(
            self.start_new, self.collected_data, self.last_dir, self.conTitr
        )  # Send data to TitrationScreen
        self.manager.current = "titration_screen"  # Switch to TitrationScreen


# Define BufferApp class inheriting from App
class BufferApp(App):
    def build(self):
        sm = ScreenManager()  # Create ScreenManager
        home_screen = HomeScreen(name="home")  # Create HomeScreen
        sm.add_widget(home_screen)  # Add HomeScreen to ScreenManager
        sm.add_widget(
            TitrationScreen(name="titration_screen")
        )  # Add TitrationScreen to ScreenManager
        sm.add_widget(
            GenBCScreen(name="gen_bc_screen")
        )  # Add GenBCScreen to ScreenManager
        sm.add_widget(
            BufferTableScreen(name="buffer_table_screen")
        )  # Add BufferTableScreen to ScreenManager
        return sm  # Return ScreenManager


# Run the app if this script is executed
if __name__ == "__main__":
    BufferApp().run()
