from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy_garden.graph import Graph, MeshLinePlot, ScatterPlot
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.window import Window
import re
import chardet
import logging
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

# Set the logging level for chardet to WARNING to suppress debug messages
logging.getLogger('chardet').setLevel(logging.WARNING)

# Load the kv file for the GUI layout
Builder.load_file('titrationscreen.kv')

# Define TitrationScreen class inheriting from Screen
class TitrationScreen(Screen):
    def __init__(self, **kwargs):
        super(TitrationScreen, self).__init__(**kwargs)
        self.collected_data = {}  # Initialize collected_data dictionary
        self.acid_data = []  # Initialize acid_data list
        self.base_data = []  # Initialize base_data list
        self.acid_file_name = None  # Initialize acid_file_name
        self.base_file_name = None  # Initialize base_file_name
        self.last_dir = ''  # Initialize last_dir
        self.conTitr = 0  # Initialize conTitr
        self.start_new = False  # Initialize start_new flag

        self.create_ui()  # Call method to create UI
        Window.bind(on_resize=self.on_window_resize)  # Bind window resize event to on_window_resize method

    # Receive data method
    def receive_data(self, start_new, data, last_dir, conTitr):
        self.start_new = start_new  # Update start_new flag
        self.collected_data = data  # Update collected_data dictionary
        self.print_collected_data()  # Print collected data

        self.last_dir = last_dir  # Update last_dir
        self.conTitr = conTitr  # Update conTitr

        if self.start_new:
            self.clear_graph()  # Clear graph if starting new
            self.acid_data = []  # Reset acid_data list
            self.base_data = []  # Reset base_data list

    # Create UI method
    def create_ui(self):
        # Set background color to white
        Window.clearcolor = (1, 1, 1, 1)
        self.graph = None  # Initialize graph attribute

    # Go back method to switch to home screen
    def go_back(self):
        self.manager.current = 'home'  # Set current screen to home

    # Method to handle window resize event
    def on_window_resize(self, instance, width, height):
        if self.graph:
            # Recalculate graph position and size on window resize
            self.graph.size = (width, height)
            self.graph.pos = (0, 0)  # Adjust position as needed
            self.update_chart()  # Update chart content

    # Method to select acid file
    def select_acid_file(self):
        self.show_file_chooser(self.load_acid_file)  # Show file chooser for acid file

    # Method to select base file
    def select_base_file(self):
        self.show_file_chooser(self.load_base_file)  # Show file chooser for base file

    # Show file chooser method
    def show_file_chooser(self, on_selection):
        filechooser = FileChooserListView(path=self.last_dir, filters=['*.RPT'])  # Create FileChooserListView
        popup = Popup(title="Select a File", content=filechooser, size_hint=(0.9, 0.9))  # Create and open popup
        filechooser.bind(on_submit=lambda *args: self.load_file(filechooser, on_selection, popup))  # Bind file selection
        popup.open()  # Open popup

    # Load file method
    def load_file(self, filechooser, on_selection, popup):
        if filechooser.selection:
            file_path = filechooser.selection[0]  # Get selected file path
            on_selection(file_path)  # Call on_selection method with file path
            popup.dismiss()  # Dismiss popup

    # Load acid file method
    def load_acid_file(self, file_path):
        self.acid_file_name = file_path.split('/')[-1]  # Extract file name
        self.acid_data = self.process_file_content(file_path)  # Process file content
        self.update_chart()  # Update chart

    # Load base file method
    def load_base_file(self, file_path):
        self.base_file_name = file_path.split('/')[-1]  # Extract file name
        self.base_data = self.process_file_content(file_path)  # Process file content
        self.update_chart()  # Update chart

    # Process file content method
    def process_file_content(self, file_path):
        data_points = []  # Initialize data points list
        with open(file_path, 'rb') as file:
            raw_data = file.read()  # Read raw data
            result = chardet.detect(raw_data)  # Detect file encoding
            encoding = result['encoding']  # Get encoding

            if encoding.lower() != 'utf-8':
                raw_data = raw_data.decode(encoding).encode('utf-8')  # Re-encode to UTF-8 if necessary

            content = raw_data.decode('utf-8')  # Decode content to string
            data_section = False
            for line in content.split('\n'):
                if line.strip().startswith("Nr Volume[mL]"):
                    data_section = True  # Start reading data section
                    continue
                if data_section:
                    parts = re.split(r'\s+', line.strip())  # Split line into parts
                    if len(parts) < 4:
                        break
                    try:
                        volume = float(parts[1])  # Parse volume
                        pH = float(parts[3])  # Parse pH
                        data_points.append((volume, pH))  # Add data point
                    except ValueError:
                        continue
        return data_points  # Return data points

    # Update chart method
    def update_chart(self):
        if not self.acid_data and not self.base_data:
            return

        self.ids.chart_layout.clear_widgets()  # Clear existing widgets from chart layout

        # Define the label options without 'font_size'
        label_options = {
            'color': [0, 0, 0, 1],
            'bold': False,
            'italic': False
        }

        xmin = 0
        xmax = max([point[0] for point in self.acid_data + self.base_data])
        x_ticks_major = (xmax - xmin) / 10 if xmax - xmin > 10 else 1

        # Set 'font_size' directly in the Graph parameters
        self.graph = Graph(
            xlabel='Volume Added (mL)', ylabel='pH',
            x_ticks_minor=5, x_ticks_major=x_ticks_major, y_ticks_minor=1, y_ticks_major=1,
            y_grid_label=True, x_grid_label=True,
            padding=5, xlog=False, ylog=False,
            x_grid=True, y_grid=True,
            border_color=[0, 0, 0, 1], draw_border=True,
            xmin=0, xmax=max([point[0] for point in self.acid_data + self.base_data]),
            ymin=0, ymax=14,
            label_options=label_options,
            font_size=dp(20)
        )

        self.graph.size_hint = (1, 1)
        self.graph.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        if self.acid_data:
            acid_line = MeshLinePlot(color=[245/255, 39/255, 103/255, 0.8])
            acid_line.points = self.acid_data  # Add acid data points to line plot
            self.graph.add_plot(acid_line)  # Add acid line plot to graph

            acid_scatter = ScatterPlot(color=[245/255, 39/255, 103/255, 0.8], point_size=5)
            acid_scatter.points = self.acid_data  # Add acid data points to scatter plot
            self.graph.add_plot(acid_scatter)  # Add acid scatter plot to graph

        if self.base_data:
            base_line = MeshLinePlot(color=[39/255, 65/255, 245/255, 0.8])
            base_line.points = self.base_data  # Add base data points to line plot
            self.graph.add_plot(base_line)  # Add base line plot to graph

            base_scatter = ScatterPlot(color=[39/255, 65/255, 245/255, 0.8], point_size=5)
            base_scatter.points = self.base_data  # Add base data points to scatter plot
            self.graph.add_plot(base_scatter)  # Add base scatter plot to graph

        # Add the new graph
        self.ids.chart_layout.add_widget(self.graph)  # Add graph to chart layout

    # Clear graph method
    def clear_graph(self):
        if self.graph:
            self.ids.chart_layout.remove_widget(self.graph)  # Remove graph from layout
            self.graph.clear_widgets()  # Clear graph widgets
            self.graph = None  # Reset graph attribute

    # Go to GenBC graph method
    def go_to_genBC_graph(self):
        # Check if the necessary data is present
        if not self.collected_data or not self.acid_data or not self.base_data:
            # If not, show a warning message to the user
            content = BoxLayout(orientation='vertical')
            content.add_widget(Label(text='Please upload the ingredient, acid, and base titration files.', font_size=20))
            ok_button = Button(text='OK')
            content.add_widget(ok_button)

            popup = Popup(title='Warning',
                          content=content,
                          size_hint=(None, None), size=(650, 300))

            ok_button.bind(on_press=popup.dismiss)  # Bind OK button to dismiss popup

            popup.open()  # Open popup
        else:
            self.manager.current = 'gen_bc_screen'  # Set current screen to gen_bc_screen
            self.manager.get_screen('gen_bc_screen').receive_data(self.collected_data, self.acid_data, self.base_data, self.conTitr)  # Pass data to gen_bc_screen

    # Print collected data method
    def print_collected_data(self):
        for key, value in self.collected_data.items():
            print(f"{key}: {value}")  # Print each key-value pair in collected_data
