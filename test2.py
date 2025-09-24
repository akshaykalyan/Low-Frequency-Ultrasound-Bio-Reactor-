from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.core.window import Window
from kivy.properties import BooleanProperty, StringProperty, ListProperty, NumericProperty
from kivy.graphics import Mesh
import random
import time
import math

# Set the window to fullscreen (for touchscreen)
Window.fullscreen = 'auto'


class MeshLinePlot(Widget):
    def __init__(self, **kwargs):
        super(MeshLinePlot, self).__init__(**kwargs)
        self.points = []
        self.color = [1, 1, 1, 1]
        self.line_width = 2

    def draw(self):
        self.canvas.clear()
        if len(self.points) < 2:
            return

        with self.canvas:
            Color(*self.color)
            Line(points=self.points, width=self.line_width)


class TemperatureGraph(Widget):
    def __init__(self, **kwargs):
        super(TemperatureGraph, self).__init__(**kwargs)

        # Initialize data
        self.time_data = []
        self.temp_data = []
        self.start_time = None
        self.is_recording = False

        # Graph properties
        self.x_min = 0
        self.x_max = 100
        self.y_min = 35
        self.y_max = 70

        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        if not self.time_data:
            return

        with self.canvas:
            # Dark background
            Color(0.12, 0.12, 0.15, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Border
            Color(0.3, 0.3, 0.35, 1)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 10), width=1.5)

            # Grid lines
            Color(0.2, 0.2, 0.25, 1)

            # Horizontal grid lines
            for i in range(1, 6):
                y = self.y + (i * self.height / 6)
                Line(points=[self.x + 40, y, self.x + self.width - 20, y], width=1)

            # Vertical grid lines (fewer for clarity)
            for i in range(1, 5):
                x = self.x + 40 + (i * (self.width - 60) / 4)
                Line(points=[x, self.y + 20, x, self.y + self.height - 20], width=1)

            # Draw axes
            Color(0.6, 0.6, 0.6, 1)
            # X-axis
            Line(points=[self.x + 40, self.y + 20, self.x + self.width - 20, self.y + 20], width=2)
            # Y-axis
            Line(points=[self.x + 40, self.y + 20, self.x + 40, self.y + self.height - 20], width=2)

            # Axis labels
            # Y-axis labels
            for i in range(7):
                temp_val = self.y_min + (i * (self.y_max - self.y_min) / 6)
                y = self.y + 20 + (i * (self.height - 40) / 6)
                Label(text=f'{temp_val:.0f}°C', pos=(self.x + 10, y - 10), size=(30, 20),
                      color=(0.8, 0.8, 0.8, 1), font_size='12sp')
                Line(points=[self.x + 38, y, self.x + 42, y], width=2)

            # X-axis labels
            if self.time_data:
                max_time = max(self.time_data)
                for i in range(5):
                    time_val = i * max_time / 4
                    x = self.x + 40 + (i * (self.width - 60) / 4)
                    Label(text=f'{time_val:.0f}s', pos=(x - 15, self.y), size=(30, 20),
                          color=(0.8, 0.8, 0.8, 1), font_size='12sp')
                    Line(points=[x, self.y + 18, x, self.y + 22], width=2)

            # Temperature line
            if len(self.time_data) > 1:
                # Main temperature line (cyan)
                Color(0.0, 0.8, 0.8, 1)
                points = []

                for i, (time_val, temp) in enumerate(zip(self.time_data, self.temp_data)):
                    x = self.x + 40 + ((time_val - self.x_min) / (self.x_max - self.x_min)) * (self.width - 60)
                    y = self.y + 20 + ((temp - self.y_min) / (self.y_max - self.y_min)) * (self.height - 40)
                    points.extend([x, y])

                Line(points=points, width=3)

                # Data points
                for i, (time_val, temp) in enumerate(zip(self.time_data, self.temp_data)):
                    x = self.x + 40 + ((time_val - self.x_min) / (self.x_max - self.x_min)) * (self.width - 60)
                    y = self.y + 20 + ((temp - self.y_min) / (self.y_max - self.y_min)) * (self.height - 40)

                    # Point outline
                    Color(0.05, 0.05, 0.07, 1)
                    Ellipse(pos=(x - 6, y - 6), size=(12, 12))

                    # Point fill (cyan)
                    Color(0.0, 0.8, 0.8, 1)
                    Ellipse(pos=(x - 4, y - 4), size=(8, 8))

    def start_recording(self):
        """Start recording temperature data"""
        self.time_data = []
        self.temp_data = []
        self.start_time = time.time()
        self.is_recording = True
        self.x_min = 0
        self.x_max = 100
        print("Temperature recording started")

    def stop_recording(self):
        """Stop recording temperature data"""
        self.is_recording = False
        print("Temperature recording stopped")

    def add_data_point(self, temperature):
        """Add a new temperature data point"""
        if self.is_recording and self.start_time is not None:
            current_time = time.time() - self.start_time
            self.time_data.append(current_time)
            self.temp_data.append(temperature)

            # Update graph limits if needed
            if current_time > self.x_max - 20:
                self.x_max = current_time + 50

            max_temp = max(self.temp_data) if self.temp_data else temperature
            min_temp = min(self.temp_data) if self.temp_data else temperature

            if max_temp > self.y_max - 5:
                self.y_max = max_temp + 10
            if min_temp < self.y_min + 5:
                self.y_min = min_temp - 5

            # Update the display
            self.update_canvas()


class StartStopToggle(BoxLayout):
    is_active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(StartStopToggle, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 16
        self.size_hint = (1, 0.2)
        self.padding = [20, 0, 20, 0]

        # Status indicator
        self.status_indicator = Widget(size_hint=(0.2, 1))
        self.update_indicator()

        # Create the toggle button
        self.toggle_btn = ToggleButton(
            text='STOP' if self.is_active else 'START',
            font_size='24sp',
            background_normal='',
            background_down='',
            background_color=(0.8, 0.2, 0.2, 1) if self.is_active else (0.2, 0.6, 0.2, 1),
            size_hint=(0.6, 1)
        )
        self.toggle_btn.bind(state=self.on_toggle)

        # Status label
        self.status_label = Label(
            text='RUNNING' if self.is_active else 'STOPPED',
            font_size='20sp',
            size_hint=(0.2, 1),
            color=(0.8, 0.2, 0.2, 1) if self.is_active else (0.2, 0.6, 0.2, 1)
        )

        self.add_widget(self.status_indicator)
        self.add_widget(self.toggle_btn)
        self.add_widget(self.status_label)

    def on_toggle(self, instance, value):
        self.is_active = value == 'down'
        self.toggle_btn.text = 'STOP' if self.is_active else 'START'
        self.toggle_btn.background_color = (0.8, 0.2, 0.2, 1) if self.is_active else (0.2, 0.6, 0.2, 1)
        self.status_label.text = 'RUNNING' if self.is_active else 'STOPPED'
        self.status_label.color = (0.8, 0.2, 0.2, 1) if self.is_active else (0.2, 0.6, 0.2, 1)
        self.update_indicator()
        print("System", "started" if self.is_active else "stopped")

    def update_indicator(self):
        self.status_indicator.canvas.clear()
        with self.status_indicator.canvas:
            if self.is_active:
                Color(0.2, 0.6, 0.2, 1)  # Green when active
            else:
                Color(0.8, 0.2, 0.2, 1)  # Red when inactive
            Ellipse(pos=(
                self.status_indicator.x + self.status_indicator.width / 2 - 15,
                self.status_indicator.y + self.status_indicator.height / 2 - 15
            ), size=(30, 30))

            # Add a subtle glow effect
            if self.is_active:
                Color(0.2, 0.6, 0.2, 0.3)
            else:
                Color(0.8, 0.2, 0.2, 0.3)
            Ellipse(pos=(
                self.status_indicator.x + self.status_indicator.width / 2 - 20,
                self.status_indicator.y + self.status_indicator.height / 2 - 20
            ), size=(40, 40))


class Dashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(Dashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 24
        self.spacing = 24

        # Set dark background color
        with self.canvas.before:
            Color(0.1, 0.1, 0.12, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Header with logo
        header = BoxLayout(orientation='horizontal', size_hint_y=0.15)

        title = Label(
            text='Low Frequency Ultrasound Bio-Reactor',
            font_size='36sp',
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        header.add_widget(title)
        self.add_widget(header)

        # Main content area
        content = BoxLayout(orientation='horizontal', spacing=24)

        # Left panel - Controls
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=16)

        # Radio buttons section - Made consistent with right panel
        radio_label = Label(
            text='Select Sound Pressure',
            font_size='28sp',
            size_hint_y=None,  # disable proportional sizing
            height=50,  # fixed pixel height
            color=(0.8, 0.8, 0.8, 1)
        )
        left_panel.add_widget(radio_label)

        # Create radio buttons with dark theme and selection color
        self.radio_buttons = []
        radio_options = ['5 kPa', '10 kPa', '30 kPa', '50 kPa']
        for option in radio_options:
            btn = ToggleButton(
                text=option,
                group='mode',
                font_size='24sp',
                background_normal='',
                background_down='',
                background_color=(0.2, 0.2, 0.25, 1),  # Dark button
                color=(0.8, 0.8, 0.8, 1)  # Light text
            )
            # Bind to update the button color when selected
            btn.bind(state=self.on_radio_state)
            btn.bind(on_press=self.radio_selected)
            self.radio_buttons.append(btn)
            left_panel.add_widget(btn)

        # Set the first button as active
        self.radio_buttons[0].state = 'down'
        self.selected_mode = radio_options[0]
        self.update_radio_colors()

        # Status display
        self.status_label = Label(
            text=f'Sound Pressure: {self.selected_mode}',
            font_size='24sp',
            size_hint_y=0.15,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )
        left_panel.add_widget(self.status_label)

        # Add left panel to content
        content.add_widget(left_panel)

        # Right panel - Graph and controls
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=16)  # Made spacing consistent

        # Operation mode radio buttons (Continuous/Pulsed)
        mode_label = Label(
            text='Select Operation Type',
            font_size='28sp',
            size_hint_y=None,  # disable proportional sizing
            height=50,  # same fixed pixel height
            color=(0.8, 0.8, 0.8, 1)
        )
        right_panel.add_widget(mode_label)

        # Create operation type radio buttons
        self.op_type_buttons = []
        op_type_options = ['CONTINUOUS', 'PULSED']
        op_type_container = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=16)  # Made height consistent

        for option in op_type_options:
            btn = ToggleButton(
                text=option,
                group='op_type',
                font_size='24sp',  # Increased font size for consistency
                background_normal='',
                background_down='',
                background_color=(0.2, 0.2, 0.25, 1),  # Dark button
                color=(0.8, 0.8, 0.8, 1)  # Light text
            )
            # Bind to update the button color when selected
            btn.bind(state=self.on_op_type_state)
            btn.bind(on_press=self.op_type_selected)
            self.op_type_buttons.append(btn)
            op_type_container.add_widget(btn)

        # Set the first button as active
        self.op_type_buttons[0].state = 'down'
        self.selected_op_type = op_type_options[0]
        self.update_op_type_colors()

        right_panel.add_widget(op_type_container)

        # Operation status display
        self.op_status_label = Label(
            text=f'Operation Type: {self.selected_op_type}',
            font_size='24sp',  # Increased font size for consistency
            size_hint_y=0.12,  # Made consistent with other labels
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )
        right_panel.add_widget(self.op_status_label)

        # System status header
        status_label = Label(
            text='Status',
            font_size='28sp',  # Increased font size for consistency
            size_hint_y=0.12,  # Made consistent with other labels
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        right_panel.add_widget(status_label)

        # Current Voltage and freq display
        volt_freq_display = BoxLayout(orientation='horizontal', size_hint_y=0.12)  # Made consistent height
        volt_text = Label(
            text='Actuation Voltage:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.volt_value = Label(
            text='45 Vrms',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )

        freq_text = Label(
            text='Frequency:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.freq_value = Label(
            text='30 kHz',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )

        volt_freq_display.add_widget(volt_text)
        volt_freq_display.add_widget(self.volt_value)
        volt_freq_display.add_widget(freq_text)
        volt_freq_display.add_widget(self.freq_value)
        right_panel.add_widget(volt_freq_display)

        # Current temperature and Load Power display
        load_temp_display = BoxLayout(orientation='horizontal', size_hint_y=0.12)  # Made consistent height
        temp_text = Label(
            text='Temperature:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.temp_value = Label(
            text='45°C',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )

        load_power_text = Label(
            text='Load Power:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.load_power_value = Label(
            text='0 W',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )

        load_temp_display.add_widget(temp_text)
        load_temp_display.add_widget(self.temp_value)
        load_temp_display.add_widget(load_power_text)
        load_temp_display.add_widget(self.load_power_value)
        right_panel.add_widget(load_temp_display)

        # Current Operation Type and Running Time
        operation_running_display = BoxLayout(orientation='horizontal', size_hint_y=0.12)  # Made consistent height
        operation_type_text = Label(
            text='Operation Type:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.operation_value = Label(
            text='Continuous',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )

        running_time_text = Label(
            text='Running Time:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.running_time_label = Label(
            text='0 s',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.0, 0.8, 0.8, 1)  # Cyan
        )

        operation_running_display.add_widget(operation_type_text)
        operation_running_display.add_widget(self.operation_value)
        operation_running_display.add_widget(running_time_text)
        operation_running_display.add_widget(self.running_time_label)
        right_panel.add_widget(operation_running_display)

        # Temperature graph
        graph_label = Label(
            text='Bio Reactor Temperature:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_y=0.12,  # Made consistent with other labels
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        right_panel.add_widget(graph_label)

        self.temp_graph = TemperatureGraph(size_hint_y=0.4)
        right_panel.add_widget(self.temp_graph)

        # Start/Stop toggle
        self.start_stop_toggle = StartStopToggle()
        right_panel.add_widget(self.start_stop_toggle)

        # Add right panel to content
        content.add_widget(right_panel)

        # Add content to main layout
        self.add_widget(content)

        # Initialize running time
        self.running_time = 0
        self.is_system_running = False

        # Schedule updates for system stats
        Clock.schedule_interval(self.update_stats, 1)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_radio_state(self, instance, value):
        self.update_radio_colors()

    def update_radio_colors(self):
        for btn in self.radio_buttons:
            if btn.state == 'down':
                btn.background_color = (0.0, 0.5, 0.5, 1)  # Cyan when selected
                btn.color = (1, 1, 1, 1)  # White text when selected
            else:
                btn.background_color = (0.2, 0.2, 0.25, 1)  # Dark when not selected
                btn.color = (0.8, 0.8, 0.8, 1)  # Light gray text when not selected

    def on_op_type_state(self, instance, value):
        self.update_op_type_colors()

    def update_op_type_colors(self):
        for btn in self.op_type_buttons:
            if btn.state == 'down':
                btn.background_color = (0.0, 0.5, 0.5, 1)  # Cyan when selected
                btn.color = (1, 1, 1, 1)  # White text when selected
            else:
                btn.background_color = (0.2, 0.2, 0.25, 1)  # Dark when not selected
                btn.color = (0.8, 0.8, 0.8, 1)  # Light gray text when not selected

    def radio_selected(self, instance):
        if instance.state == 'down':
            self.selected_mode = instance.text
            self.status_label.text = f'Sound Pressure: {self.selected_mode}'

    def op_type_selected(self, instance):
        if instance.state == 'down':
            self.selected_op_type = instance.text
            self.op_status_label.text = f'Operation Type: {self.selected_op_type}'
            self.operation_value.text = self.selected_op_type

    def update_stats(self, dt):
        # Check if system is running
        if self.start_stop_toggle.is_active:
            if not self.is_system_running:
                # System just started
                self.is_system_running = True
                self.running_time = 0
                self.temp_graph.start_recording()

            # Update running time
            self.running_time += 1
            self.running_time_label.text = f'{self.running_time} s'

            # Generate new temperature data (simulated)
            new_temp = random.randint(40, 65)
            self.temp_value.text = f'{new_temp}°C'

            # Update temperature graph
            self.temp_graph.add_data_point(new_temp)

            # Update other simulated values
            self.freq_value.text = f'{random.randint(20, 40)} kHz'
            self.load_power_value.text = f'{random.randint(50, 150)} W'
            self.volt_value.text = f'{random.randint(40, 60)} Vrms'
        else:
            if self.is_system_running:
                # System just stopped
                self.is_system_running = False
                self.temp_graph.stop_recording()


class DashboardApp(App):
    def build(self):
        return Dashboard()


if __name__ == '__main__':
    DashboardApp().run()