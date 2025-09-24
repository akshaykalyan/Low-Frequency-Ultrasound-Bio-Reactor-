import traceback

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.core.window import Window
from kivy.properties import BooleanProperty, StringProperty, ListProperty, NumericProperty
import random
from kivy.core.text import Label as CoreLabel

import serial
import time
from struct import *
import subprocess
import threading


# Set the window to fullscreen (for touchscreen)
Window.fullscreen = 'auto'
loop_stop = False

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
        self.x_min = 0.0
        self.x_max = 100.0
        self.y_min = 35.0
        self.y_max = 70.0

        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()

        # geometry helpers
        x0 = self.x + 40
        y0 = self.y + 20
        drawable_w = max(self.width - 60, 10)
        drawable_h = max(self.height - 40, 10)

        with self.canvas:
            # Background
            Color(0.12, 0.12, 0.15, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Border
            Color(0.3, 0.3, 0.35, 1)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 10), width=1.5)

            # Grid lines (horizontal)
            Color(0.2, 0.2, 0.25, 1)
            for i in range(1, 6):
                y = y0 + i * (drawable_h / 6.0)
                Line(points=[x0, y, x0 + drawable_w, y], width=1)

            # Vertical grid lines
            for i in range(1, 5):
                x = x0 + i * (drawable_w / 4.0)
                Line(points=[x, y0, x, y0 + drawable_h], width=1)

            # Axes
            Color(0.6, 0.6, 0.6, 1)
            Line(points=[x0, y0, x0 + drawable_w, y0], width=2)  # X-axis
            Line(points=[x0, y0, x0, y0 + drawable_h], width=2)  # Y-axis

            # --- Y-axis labels & ticks ---
            # Draw 7 labels for Y (including min/max)
            for i in range(7):
                temp_val = self.y_min + (i * (self.y_max - self.y_min) / 6.0)
                y = y0 + (i * (drawable_h / 6.0))

                # tick mark
                Color(0.6, 0.6, 0.6, 1)
                Line(points=[x0 - 6, y, x0 - 1, y], width=2)

                # label as texture
                lbl = CoreLabel(text=f'{temp_val:.0f}°C', font_size=12)
                lbl.refresh()
                tex = lbl.texture
                # label color (draw the label texture with a light color)
                Color(0.8, 0.8, 0.8, 1)
                Rectangle(texture=tex, pos=(x0 - tex.width - 10, y - tex.height / 2.0), size=tex.size)

            # --- X-axis labels & ticks ---
            # Make ticks match the visible range (x_min -> x_max)
            dx = (self.x_max - self.x_min) if (self.x_max - self.x_min) != 0 else 1.0
            for i in range(5):
                tick_time = self.x_min + (i * dx / 4.0)  # evenly spaced in current visible range
                # compute x position using same transform used for plotting
                x = x0 + ((tick_time - self.x_min) / dx) * drawable_w

                # vertical tick mark
                Color(0.6, 0.6, 0.6, 1)
                Line(points=[x, y0 - 2, x, y0 + 6], width=2)

                # label texture (centered)
                lbl = CoreLabel(text=f'{tick_time:.0f}s', font_size=12)
                lbl.refresh()
                tex = lbl.texture
                Color(0.8, 0.8, 0.8, 1)
                Rectangle(texture=tex, pos=(x - tex.width / 2.0, y0 - tex.height - 4), size=tex.size)

            # --- Temperature line and points ---
            if len(self.time_data) > 1:
                # Main line
                Color(0.0, 0.8, 0.8, 1)
                points = []

                y_span = (self.y_max - self.y_min) if (self.y_max - self.y_min) != 0 else 1.0

                for time_val, temp in zip(self.time_data, self.temp_data):
                    sx = x0 + ((time_val - self.x_min) / dx) * drawable_w
                    sy = y0 + ((temp - self.y_min) / y_span) * drawable_h
                    # optional clamp to plotting area to avoid stray points off-canvas
                    sx = min(max(sx, x0), x0 + drawable_w)
                    sy = min(max(sy, y0), y0 + drawable_h)
                    points.extend([sx, sy])

                Line(points=points, width=3)

                # draw points
                for time_val, temp in zip(self.time_data, self.temp_data):
                    sx = x0 + ((time_val - self.x_min) / dx) * drawable_w
                    sy = y0 + ((temp - self.y_min) / y_span) * drawable_h
                    Color(0.05, 0.05, 0.07, 1)
                    Ellipse(pos=(sx - 6, sy - 6), size=(12, 12))
                    Color(0.0, 0.8, 0.8, 1)
                    Ellipse(pos=(sx - 4, sy - 4), size=(8, 8))

    def start_recording(self):
        """Start recording temperature data"""
        self.time_data = []
        self.temp_data = []
        self.start_time = time.time()
        self.is_recording = True
        self.x_min = 0.0
        self.x_max = 100.0
        self.update_canvas()

    def stop_recording(self):
        """Stop recording temperature data"""
        self.is_recording = False
        print("Temperature recording stopped")
        self.update_canvas()

    def add_data_point(self, temperature):
        """Add a new temperature data point"""
        if self.is_recording and self.start_time is not None:
            current_time = time.time() - self.start_time
            self.time_data.append(current_time)
            self.temp_data.append(temperature)

            # Update graph limits if needed (same strategy as before)
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
        self.dashboard = kwargs.pop('dashboard', None)  # store reference
        super(StartStopToggle, self).__init__(**kwargs)

        self.orientation = 'horizontal'
        self.spacing = 16
        self.size_hint = (1, 0.2)
        self.padding = [20, 0, 20, 0]

        # Toggle button
        self.toggle_btn = ToggleButton(
            text='START',
            font_size='24sp',
            background_normal='',
            background_down='',
            background_color=(0.2, 0.6, 0.2, 1),
            size_hint=(0.6, 1)
        )
        self.toggle_btn.bind(state=self.on_toggle)

        # Status label
        self.status_label = Label(
            text='STOPPED',
            font_size='24sp',
            size_hint=(0.2, 1),
            color=(0.2, 0.6, 0.2, 1)
        )

        self.add_widget(self.toggle_btn)
        self.add_widget(self.status_label)

    def on_toggle(self, instance, value):
        self.is_active = value == 'down'
        self.toggle_btn.text = 'STOP' if self.is_active else 'START'
        self.toggle_btn.background_color = (0.8, 0.2, 0.2, 1) if self.is_active else (0.2, 0.6, 0.2, 1)
        self.status_label.text = 'RUNNING' if self.is_active else 'STOPPED'
        self.status_label.color = (0.8, 0.2, 0.2, 1) if self.is_active else (0.2, 0.6, 0.2, 1)
        print("System", "started" if self.is_active else "stopped")

        # 🔹 Control async loop
        if self.dashboard:
            if self.is_active:  # START pressed
                self.dashboard.start_async_loop()
            else:  # STOP pressed
                self.dashboard.stop_async_loop()


class Dashboard(BoxLayout):
    global volt
    def __init__(self, **kwargs):
        super(Dashboard, self).__init__(**kwargs)
        self.start_stop_toggle = StartStopToggle(dashboard=self)

        self.loop_thread = None
        self.loop_running = False
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
            size_hint_y=.12,  # disable proportional sizing
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

        # System status header
        status_label = Label(
            text='Status',
            font_size='28sp',  # Increased font size for consistency
            size_hint_y=0.12,  # Made consistent with other labels
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )

        # Current Voltage and freq display
        volt_freq_display = BoxLayout(orientation='horizontal', size_hint_y=0.12)  # Made consistent height
        volt_text = Label(
            text='Actuation Voltage:',
            font_size='24sp',  # Increased font size for consistency
            size_hint_x=0.6,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.volt_value = Label(
            text=f'{volt} Vrms',
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



        # Add right panel to content
        content.add_widget(right_panel)

        # Add content to main layout
        self.add_widget(content)

        # Initialize running time
        self.running_time = 0
        self.is_system_running = False

        # Schedule updates for system stats
        Clock.schedule_interval(self.update_stats, 1)

        right_panel.add_widget(self.start_stop_toggle)

    def start_async_loop(self):
        """Start background loop"""
        print("Starting background loop")

        if self.loop_thread and self.loop_thread.is_alive():
            print("Background loop already running")
            return  # already running
        loop_stop = False
        self.loop_running = True
        update('ENABLE', '')

        def worker():
            while self.loop_running:
                print()
                if self.operation_value.text == 'PULSED':
                    start_pulsing(volt)
                else:
                    set_voltage(volt)
        self.loop_thread = threading.Thread(target=worker, daemon=True)
        self.loop_thread.start()

    def stop_async_loop(self):
        """Stop background loop"""
        self.loop_running = False
        loop_stop =True
        self.loop_thread = None
        stop()

    def on_loop_result(self, result):
        """Handle loop output on UI thread"""
        print("Loop output:", result)


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
        calibration_data ={5:10,10:25,30:75,50:100}
        if instance.state == 'down':
            self.selected_mode = instance.text
            self.status_label.text = f'Sound Pressure: {self.selected_mode}'
            select_v =  int(self.selected_mode[:-3])
            set_voltage(calibration_data[select_v])


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
            self.running_time += .5
            self.running_time_label.text = f'{self.running_time} s'

            # Generate new temperature data (simulated)
            new_temp = random.randint(40, 65)
            # self.temp_value.text = f'{new_temp}°C'

            # Update temperature graphcon
            self.temp_graph.add_data_point(new_temp)

            # Update other simulated values
            self.freq_value.text = f'40 kHz'
            # self.load_power_value.text = f'{ampState.loadPower} W'
            self.volt_value.text = f'{volt} Vrms'
        else:
            if self.is_system_running:
                # System just stopped
                self.is_system_running = False
                self.temp_graph.stop_recording()
ser = serial.Serial(port='COM3', baudrate=9600, timeout=1)
is_pulsed = True
volt = 0
freq = 40000
class AmpliferState:

    is_pulsed = True
    start_flag = False
    def __init__(self, data):
        print(data)
        self.enabled = bool(data[0])
        self.phaseTracking = bool(data[1])
        self.currentTracking = bool(data[2])
        self.powerTracking = bool(data[3])
        self.errorAmp = bool(data[4])
        self.errorLoad = bool(data[5])
        self.errorTemperature = bool(data[6])
        self.voltage = float(unpack('f', data[8:12])[0])
        self.frequency = float(unpack('f', data[12:16])[0])
        self.minFrequency = float(unpack('f', data[16:20])[0])
        self.maxFrequency = float(unpack('f', data[20:24])[0])
        self.phaseSetpoint = float(unpack('f', data[24:28])[0])
        self.phaseControlGain = float(unpack('f', data[28:32])[0])
        self.currentSetpoint = float(unpack('f', data[32:36])[0])
        self.currentControlGain = float(unpack('f', data[36:40])[0])
        self.powerSetpoint = float(unpack('f', data[40:44])[0])
        self.powerControlGain = float(unpack('f', data[44:48])[0])
        self.maxLoadPower = float(unpack('f', data[48:52])[0])
        self.ampliferPower = float(unpack('f', data[52:56])[0])
        self.loadPower = float(unpack('f', data[56:60])[0])
        self.temperature = float(unpack('f', data[60:64])[0])
        self.measuredPhase = float(unpack('f', data[64:68])[0])
        self.measuredCurrent = float(unpack('f', data[68:72])[0])
        self.Impedance = float(unpack('f', data[72:76])[0])
        self.transformerTruns = float(unpack('f', data[76:80])[0])


def update(command, value):
    ser.write((command + value + '\r').encode())
    ser.read_until('\r'.encode())

def getAmplifierState():
    ser.flushInput()
    ser.write('getSTATE\r'.encode())
    returned = ser.read(80)
    ser.flushInput()
    amplifer = AmpliferState(returned)
    return amplifer


def set_pressure(pressure):
    pass

def set_voltage(voltage):
    global volt
    volt = voltage
    update('setVOLT', str(voltage))

def set_freq(freq):
    update('setFREQ', str(freq))


def get_load_power():
    amplifier_state = getAmplifierState()
    return  amplifier_state.loadPower

def get_voltage():
    amplifier_state = getAmplifierState()
    return  amplifier_state.voltage

def start_pulsing(volt):
    set_voltage(volt)
    time.sleep(1)
    update('setVOLT', str(0))
    time.sleep(1)

def stop():
    print("stop")
    # amplifier_state = getAmplifierState()
    update('DISABLE', '')

set_voltage(10)

class DashboardApp(App):
    def build(self):
        return Dashboard()

if __name__ == '__main__':
    DashboardApp().run()

    # try:
    # except Exception as e:
    #     # print(e)
    #     # print('error')
    #     # ser.close()`
    #