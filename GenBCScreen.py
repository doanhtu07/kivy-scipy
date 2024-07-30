import os
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy_garden.graph import Graph, MeshLinePlot, ScatterPlot, LinePlot
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.textinput import TextInput
import numpy as np
from kivy.uix.boxlayout import BoxLayout
from ModelBC import pyModelBCCurve
from kivy.graphics import Mesh, Color, Line, Rectangle
from getAdjct import pyGetAdjCT, CalcError, CalcpH_ABT, getFx, getFp, adjpka
from GenBC import pyGenBCCurve, tCurve, fillGaps
from WaterCurve import genWater
from kivy.uix.checkbox import CheckBox
import csv
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup


#global Buffer Capacity array, BC
BC = None
oriBC = None
fillBC = None
orifillBC = None
measuredpH = -1
buftable = None
acid_x = None
acid_y = None
base_x = None
base_y = None
WC = None
def set_globals(key, value):
   globals()[key] = value

# Define the class GenBCScreen which inherits from Screen
class GenBCScreen(Screen):
    # Initialize the class with additional keyword arguments
    def __init__(self, **kwargs):
        # Call the parent class's constructor
        super(GenBCScreen, self).__init__(**kwargs)
        # Initialize instance variables
        self.collected_data = {}
        self.conTitr = 0
        self.electrode_shift = 0
        self.acid_data = []
        self.base_data = []
        self.start_new = False
        self.adjC = 0  # Define the variable "adjC"
        self.pH = None # Define the variable "pH"
        self.adjC_formatted = None
        self.sse_formatted = None
        self.tbeta_formatted = None

    # Define a method to receive data and process it
    def receive_data(self, collected_data, acid_data, base_data, conTitr):
        self.collected_data = collected_data
        self.acid_data = acid_data
        self.base_data = base_data
        self.conTitr = conTitr
        self.create_input_boxes()
        self.preGenBC(self.collected_data, self.acid_data, self.base_data)

    # Define a method to preprocess data for generating a BC curve
    def preGenBC(self, collected_data, acid_data, base_data):
        init_vol = collected_data.get("init_vol")
        molHCl = collected_data.get("molHCl")
        molNaOH = collected_data.get("molNaOH")
        removeVal = collected_data.get("removeVal")
        mingaps = collected_data.get("mingap")
        increment = collected_data.get("increment")
        NaClPercent = collected_data.get("nacl")
        self.trim_beg_initial = collected_data.get("trim_beg")
        self.trim_end_initial = collected_data.get("trim_end")
        self.electrode_shift_initial = 0

        acid_x = [pair[0] for pair in acid_data]
        acid_y = [pair[1] for pair in acid_data]
        base_x = [pair[0] for pair in base_data]
        base_y = [pair[1] for pair in base_data]

        set_globals("measuredpH", (acid_y[0] + base_y[0])/2)
        D2B, oriBC, fillBC = pyGenBCCurve(float(init_vol), float(molHCl), float(molNaOH), float(removeVal), float(mingaps), float(increment), acid_x, acid_y, base_x, base_y)

        set_globals("oriBC", oriBC)
        set_globals("BC", oriBC)
        set_globals("fillBC", fillBC)
        set_globals("orifillBC", fillBC)

        maxBC = np.amax(BC[:, 1])
        WC = genWater(maxBC, float(NaClPercent), 1.5, 12.5)

        set_globals("WC", WC)
        self.create_graph(oriBC, fillBC, WC)

    # Define a method to preprocess data for modeling a BC curve
    def preModelBC(self, collected_data, acid_data, base_data):
        order = collected_data.get("order")
        npks = collected_data.get("npKs")
        pK_tol = collected_data.get("pK_tol")
        NaClPercent = collected_data.get("nacl")
        lb = collected_data.get("lB")
        ub = collected_data.get("uB")
        minConc = collected_data.get("minConc")

        X0 = [pair[0] for pair in oriBC]
        Y0 = [pair[1] for pair in oriBC]
                        
        X1 = [pair[0] for pair in fillBC]
        Y1 = [pair[1] for pair in fillBC]

        X = np.hstack((X0, X1))
        Y = np.hstack((Y0, Y1))

        Y = Y[np.argsort(X)]
        X.sort()

        buftable, tbetainfo, SPX = pyModelBCCurve(int(order), int(npks), minConc, pK_tol, float(NaClPercent), int(lb), int(ub), X, Y)#python, ModelBC.py

        set_globals("buftable", buftable)
        bcmat = tbetainfo["BCCurve"]
        maxBC = np.amax(BC)
        if SPX["BCmat"][0, 0] != 0:
            newWC = tbetainfo["waterCurve"]
        else:
            newWC = self.genWater(maxBC, NaClPercent, 1, 13)

        self.create_graph(oriBC, fillBC, WC, bcmat, newWC)
        self.sse_formatted = self.number_cleanup(SPX["SSE"], -3)
        self.model_sse_label.text = f"Model SSE: {self.sse_formatted}"

        self.tbeta_formatted = self.number_cleanup(tbetainfo["tBeta"])
        self.tbeta_label.text = f"tBeta: {self.tbeta_formatted}"
        self.useAdjCT()

    # Define a method to create a graph
    def create_graph(self, oriBC, fillBC, WC, bcmat=None, newWC=None):
        label_options = {
            'color': [0, 0, 0, 1],
            'bold': False,
            'italic': False
        }
        maxY = float(np.amax(oriBC[:, 1]))
        maxWCY = float(np.amax(WC[:, 1]))

        max_tick_value = max(maxY, maxWCY) + 0.005

        self.graph = Graph(
            xlabel='pH', ylabel='Beta', x_ticks_minor=0.5, x_ticks_major=1, y_ticks_minor=5, y_ticks_major=0.02,
            y_grid_label=True, x_grid_label=True, padding=5, x_grid=True, y_grid=True,
            border_color=[0, 0, 0, 1], draw_border=True,
            xmin=0, xmax=14, ymin=0, ymax=(max(maxY, maxWCY) + 0.005), background_color=[1, 1, 1, 1], xlog=False, ylog=False,
            label_options=label_options, font_size=dp(20)
        )
        self.graph.size_hint = (1, 1)

        if np.any(oriBC):
            oriBC_line = MeshLinePlot(color=[1, 1, 1, 1])
            oriBC_line.points = oriBC
            self.graph.add_plot(oriBC_line)

            oriBC_scatter = ScatterPlot(color=[1, 0, 0, 1], point_size=5)
            oriBC_scatter.points = oriBC
            self.graph.add_plot(oriBC_scatter)


        if np.any(fillBC):
            fillBC_line = MeshLinePlot(color=[1, 1, 1, 1])
            fillBC_line.points = fillBC
            self.graph.add_plot(fillBC_line)

            fillBC_scatter = ScatterPlot(color=[1, 0.5, 0, 1], point_size=5)
            fillBC_scatter.points = fillBC
            self.graph.add_plot(fillBC_scatter)


        if np.any(WC):
            WC_line = MeshLinePlot(color=[1, 1, 1, 1])
            WC_line.points = WC
            self.graph.add_plot(WC_line)

            WC_scatter = ScatterPlot(color=[0, 0, 1, 1], point_size=5)
            WC_scatter.points = WC
            self.graph.add_plot(WC_scatter)


        if bcmat is not None:
            bcmat_line = LinePlot(color=[0.5, 0, 0.5, 1], line_width=2)  # Purple color for bcmat
            bcmat_line.points = bcmat
            self.graph.add_plot(bcmat_line)

        if newWC is not None:
            newWC_line = LinePlot(color=[41/255, 237/255, 255/255, 0.8], line_width=2)  # Light gray color for new WC
            newWC_line.points = newWC
            self.graph.add_plot(newWC_line)


        self.clear_widgets()
        self.main_layout = BoxLayout(orientation='vertical', padding=[20, 0, 20, 20], spacing=10, height=Window.height)
        self.add_widget(self.main_layout)

        self.input_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=300, pos_hint={'top': 0.9})
        if self.layout.parent:
            self.layout.parent.remove_widget(self.layout)
        self.input_layout.add_widget(self.layout)
        self.main_layout.add_widget(self.input_layout)

        # Create a new vertical BoxLayout
        self.label_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=200, pos_hint={'center_x': 0.2, 'top': 0.8}, opacity=0)

        # Ensure checkbox layout is also added here if necessary
        self.checkbox_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        self.checkbox_label = Label(text="Use AdjC", font_size=20, bold=True, color=(0.1, 0.1, 0.1, 1), valign='center', halign='right', size_hint_y=None, height=40)
        self.checkbox = CheckBox(size_hint_x=0.1)
        self.checkbox.bind(active=self.on_checkbox_active)
        self.checkbox_layout.add_widget(self.checkbox_label)
        self.checkbox_layout.add_widget(self.checkbox)

        # Add the checkbox layout to the new label layout
        self.label_layout.add_widget(self.checkbox_layout)

        # Create the labels
        self.model_sse_label = Label(text=f"Model SSE: {self.sse_formatted if self.sse_formatted is not None else ''}", font_size=20, bold=True, color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=40)
        self.estimated_ph_label = Label(text=f"Estimated pH: {self.pH if self.pH is not None else ''}", font_size=20, bold=True, color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=40)
        self.adjc_value_label = Label(text=f"AdjC Value (M): {self.adjC_formatted if self.adjC_formatted is not None else ''}", font_size=20, bold=True, color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=40)
        self.tbeta_label = Label(text=f"tBeta: {self.tbeta_formatted if self.tbeta_formatted is not None else ''}", font_size=20, bold=True, color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=40)

        # Add the label to the new label layout
        self.label_layout.add_widget(self.model_sse_label)
        self.label_layout.add_widget(self.estimated_ph_label)
        self.label_layout.add_widget(self.adjc_value_label)
        self.label_layout.add_widget(self.tbeta_label)

        # Add the new label layout to the main layout
        self.main_layout.add_widget(self.label_layout)

        self.graph_layout = BoxLayout(height=dp(400))
        self.graph_layout.add_widget(self.graph)
        self.main_layout.add_widget(self.graph_layout)

        self.download_button = Button(
            text="Download Results File",
            size_hint=(1, None),
            height=40,
            bold=True,
            background_normal='',
            background_color=(0.05, 0.53, 0.11, 1),
            color=(1, 1, 1, 1),
            opacity=0
        )
        self.download_button.bind(on_press=self.download_results)
        self.main_layout.add_widget(self.download_button)

        self.restart_button = Button(
            text="Start Another Ingerdient",
            size_hint=(1, None),
            height=40,
            bold=True,
            background_normal='',
            background_color=(0.05, 0.53, 0.11, 1),
            color=(1, 1, 1, 1),
        )

        self.restart_button.bind(on_press=self.on_restart_button_click)
        self.main_layout.add_widget(self.restart_button)

    # Define a method to restart the process
    def on_restart_button_click(self, instance):
        self.manager.current = "home"
        self.start_new = True
        self.manager.get_screen('home').receive_data(self.start_new)

    # Define a method to create input boxes for user input
    def create_input_boxes(self):
        # Create the main layout
        self.layout = BoxLayout(orientation='vertical', spacing=10)

        # Create the input boxes with labels using a helper function
        self.trim_beg_box, self.trim_beg_input = self.create_labeled_input_box('Trim Begin:', self.collected_data.get("trim_beg", ""), self.on_trim_beg_input)
        self.trim_end_box, self.trim_end_input = self.create_labeled_input_box('Trim End:', self.collected_data.get("trim_end", ""), self.on_trim_end_input)
        self.electrode_shift_box, self.electrode_shift_input = self.create_labeled_input_box('Electrode Shift +/- 0.5:', "0", self.on_electrode_shift_input)


        # Add the input boxes to the layout
        self.layout.add_widget(self.trim_beg_box)
        self.layout.add_widget(self.trim_end_box)
        self.layout.add_widget(self.electrode_shift_box)


        # Create "Model BC Curve" button
        self.model_bc_button = Button(
            text="Model BC",
            size_hint=(1, None),
            height=40,
            bold=True,
            background_normal='',
            background_color=(0.05, 0.53, 0.11, 1),
            color=(1, 1, 1, 1),
            on_press=lambda instance: setattr(self.view_buffer_table_button, 'opacity', 1)
        )
        self.model_bc_button.bind(on_release=self.on_model_bc_button_click)
        self.layout.add_widget(self.model_bc_button)
        self.view_buffer_table_button = Button(
            text="View Buffer Table Results",
            size_hint=(1, None),
            height=40,
            bold=True,
            background_normal='',
            background_color=(0.05, 0.53, 0.11, 1),
            color=(1, 1, 1, 1),
            opacity=0
        )       
        self.view_buffer_table_button.bind(on_release=self.on_view_buffer_table_button_click)
        # Add the layout to the main widget
        self.layout.add_widget(self.view_buffer_table_button)
        self.add_widget(self.layout)

    # Define a method to show a save dialog
    def show_save_dialog(self, on_selection):
            content = BoxLayout(orientation='vertical')
            filechooser = FileChooserListView(path='/')
            filename_input = TextInput(hint_text="Enter filename",size_hint_y=None, height=45)
            content.add_widget(filechooser)
            content.add_widget(filename_input)
            save_button = Button(text='Save', size_hint_y=None, height=40)
            save_button.bind(on_press=lambda x: on_selection(filechooser.path, filename_input.text))
            content.add_widget(save_button)
            self.popup = Popup(title="Save File", content=content, size_hint=(0.9, 0.9))
            self.popup.open()

    # Define a method to download the results
    def download_results(self, instance):
            def save_file(path, filename):
                if filename:
                    with open(os.path.join(path, filename), 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(["Parameter", "Value"])
                        for key, value in self.collected_data.items():
                            writer.writerow([key, value])
                        writer.writerow(["conTitr", self.conTitr])
                        row_titles = ["Consc", "pK", "a/b"]
                        for i, row in enumerate(buftable[:3]):
                            writer.writerow([row_titles[i]] + row)
                        writer.writerow(["estimated_pH", self.pH_formatted])
                        writer.writerow(["adjC_value", self.adjC_formatted])
                        writer.writerow(["tBeta", self.tbeta_formatted])
                        writer.writerow(["trim_begin_altered", self.trim_beg_input.text])
                        writer.writerow(["trim_end_altered", self.trim_end_input.text])
                    self.popup.dismiss()

            self.show_save_dialog(save_file)

    # Define a method to handle the model BC button click
    def on_model_bc_button_click(self, instance):
        # Reset input boxes to original values
        self.trim_beg_input.text = str(self.collected_data.get("trim_beg", ""))
        self.trim_end_input.text = str(self.collected_data.get("trim_end", ""))
        self.electrode_shift_input.text = "0"

        # Call the preModelBC method
        self.preModelBC(self.collected_data, self.acid_data, self.base_data)
            # Show the buffer table button
        self.view_buffer_table_button.opacity = 1
        self.download_button.opacity = 1
        self.label_layout.opacity = 1
    
    # Define a method to create a labeled input box
    def create_labeled_input_box(self, label_text, input_text, input_callback):
        box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)

        label = Label(text=label_text, font_size=20, bold=True, color=(0.1, 0.1, 0.1, 1), size_hint_x=0.3)
        text_input = TextInput(text=str(input_text), multiline=False, input_filter='float', font_size=20, size_hint_x=0.5)
        text_input.bind(text=input_callback)

        box.add_widget(label)
        box.add_widget(text_input)

        return box, text_input
    
    # Define a method to handle the trim begin input
    def on_trim_beg_input(self, instance, value):
        try:
            self.collected_data['trim_beg'] = float(value)
            self.shift_trim_graph()
        except ValueError:
            pass

    # Define a method to handle the trim end input
    def on_trim_end_input(self, instance, value):
        try:
            self.collected_data['trim_end'] = float(value)
            self.shift_trim_graph()
        except ValueError:
            pass

    # Define a method to handle the electrode shift input
    def on_electrode_shift_input(self, instance, value):
        try:
            self.electrode_shift = float(value)
            self.shift_trim_graph()
        except ValueError:
            pass
    
    # Define a method to shift and trim the graph
    def shift_trim_graph(self):
        trimbeg = self.collected_data.get("trim_beg")
        trimend = self.collected_data.get("trim_end")
        shift = self.electrode_shift

        [BCpts, cols] = oriBC.shape

        if trimbeg+trimend <= BCpts:
            set_globals("BC", oriBC[range(int(trimbeg), BCpts), :])
            [BCpts, cols] = BC.shape
            BC[:, 0] += shift
            set_globals("BC", BC[range(int(BCpts-trimend)), :])
            maxBC = np.amax(BC[:,1])
            newFill = np.zeros(orifillBC.shape)
            newFill[:,0] += shift
            set_globals("fillBC", orifillBC + newFill)

        self.create_graph(BC,fillBC,  WC)

    # Define a method to handle the view buffer table button click
    def on_view_buffer_table_button_click(self, instance):
        self.manager.get_screen('buffer_table_screen').receive_data(buftable)
        self.manager.current = 'buffer_table_screen'

    # Define a method to handle the checkbox active state
    def on_checkbox_active(self,instance, value):
            if value:
                adjC_results = pyGetAdjCT(measuredpH, buftable, float(self.collected_data.get("nacl")))  # python, found in getAdjCT.py
                self.adjC = adjC_results.x[0]
                self.adjC_formatted = self.number_cleanup(self.adjC)
                self.adjc_value_label.text = f"AdjC Value (M): {self.adjC_formatted}"
            else:
                self.adjC = 0
                self.adjc_value_label.text = f"AdjC Value (M): {''}"
            self.pH = CalcpH_ABT(buftable, float(self.collected_data.get("nacl")), self.adjC)
            self.pH_formatted = self.number_cleanup(self.pH)
            self.estimated_ph_label.text = f"Estimated pH: {self.pH_formatted}"

    # Define a method to use the adjCT
    def useAdjCT(self):
        self.pH = CalcpH_ABT(buftable, float(self.collected_data.get("nacl")), self.adjC)
        self.pH_formatted = self.number_cleanup(self.pH)
        self.estimated_ph_label.text = f"Estimated pH: {self.pH_formatted}"
    
    # Define a method to format numbers
    def number_cleanup(self, value, preexp=None):
        if preexp is None:
            preexp = 4

        if preexp < 0:
            # Format the number in exponential notation
            formatted_value = "{:.{}e}".format(value, -preexp)
        else:
            # Format the number to the specified precision
            formatted_value = "{:.{}f}".format(value, preexp)
        return formatted_value