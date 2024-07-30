from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout

# Load the kv file for the GUI layout
Builder.load_file('buffertable.kv')

# Define BufferTableScreen class inheriting from Screen
class BufferTableScreen(Screen):
    # Initialize method
    def __init__(self, **kwargs):
        super(BufferTableScreen, self).__init__(**kwargs)
        self.buftable = {}

    # Receive data method
    def receive_data(self, buftable):
        self.buftable = buftable
        print(self.buftable)
        self.create_table()

    # Create table method
    def create_table(self):
        scroll_view = self.ids.scroll_view
        table_layout = self.ids.table_layout
        table_layout.clear_widgets()

        headers = ['Consc (M)', 'pK', 'a/b', 'Beta']
        for header in headers:
            label = Label(text=header, size_hint_y=None, height=40, font_size=30, color=(0, 0, 0, 1), bold=True)
            table_layout.add_widget(label)

        # Populate the table with data from buftable
        for row in zip(*self.buftable):
            for i, cell in enumerate(row):
                # If the cell is in the 1st, 2nd, or 4th column and is a float, round it
                if i in [0, 1, 3] and isinstance(cell, float):
                    cell = round(cell, 4)
                label = Label(text=str(cell), size_hint_y=None, height=40, font_size=25, color=(0, 0, 0, 1))
                table_layout.add_widget(label)

        # Calculate the total height of the GridLayout
        table_layout.height = len(self.buftable) * dp(30) + len(headers) * 40

        # Update the ScrollView's height
        scroll_view.height = table_layout.height