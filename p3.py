import RPi.GPIO as GPIO
import time
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# Set dark theme colors
Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Dark background

class TB6600_Stepper:
    def __init__(self, pul_pin, dir_pin, ena_pin=None):
        self.PUL = pul_pin
        self.DIR = dir_pin
        self.ENA = ena_pin

        self.steps_per_rev = 200  # SW 3 & SW 6 is OFF 200
        self.microsteps = 1
        self.delay = 0.0025
        self.pulse_state = False
        self.last_pulse_time = 0

        try:
            # Use BOARD numbering instead of BCM to avoid conflicts
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)  # Disable warnings

            # Set up pins
            GPIO.setup(self.PUL, GPIO.OUT)
            GPIO.setup(self.DIR, GPIO.OUT)

            if self.ENA is not None:
                GPIO.setup(self.ENA, GPIO.OUT)
                self.disable()

            # Initialize to LOW
            GPIO.output(self.PUL, GPIO.LOW)
            GPIO.output(self.DIR, GPIO.LOW)

            print(f"Stepper initialized on pins PUL:{pul_pin}, DIR:{dir_pin}")

        except Exception as e:
            print(f"Initialization error: {e}")
            raise

    def enable(self):
        if self.ENA is not None:
            GPIO.output(self.ENA, GPIO.LOW)  # Active low

    def disable(self):
        if self.ENA is not None:
            GPIO.output(self.ENA, GPIO.HIGH)

    def set_direction(self, direction):
        GPIO.output(self.DIR, GPIO.HIGH if direction else GPIO.LOW)

    def set_rpm(self, rpm):
        if rpm <= 0:
            raise ValueError("RPM must be greater than 0")
        self.delay = 30 / (self.steps_per_rev * rpm)

    def get_rpm(self):
        return 60 / (self.steps_per_rev * self.delay)

    def step(self, steps=1):
        if steps == 0:
            return

        direction = steps > 0
        steps = abs(steps)

        self.enable()
        self.set_direction(direction)

        print(f"Moving {steps} steps {'forward' if direction else 'backward'}")

        for i in range(steps):
            GPIO.output(self.PUL, GPIO.HIGH)
            time.sleep(self.delay)
            GPIO.output(self.PUL, GPIO.LOW)
            time.sleep(self.delay)

            # Show progress every 50 steps
            if (i + 1) % 50 == 0:
                print(f"Completed {i + 1}/{steps} steps")

    def rotate_degrees(self, degrees, direction=True):
        steps = int((degrees / 360) * self.steps_per_rev * self.microsteps)
        self.step(steps if direction else -steps)

    def generate_pulse(self, current_time):
        """Generate one pulse cycle - non-blocking version"""
        if current_time - self.last_pulse_time >= self.delay:
            self.pulse_state = not self.pulse_state
            GPIO.output(self.PUL, GPIO.HIGH if self.pulse_state else GPIO.LOW)
            if not self.pulse_state:  # Only update time after complete cycle (HIGH→LOW)
                self.last_pulse_time = current_time
            return True
        return False

    def cleanup(self):
        self.disable()
        GPIO.cleanup()
        print("GPIO cleanup completed")


class StepperControlPanel(BoxLayout):
    def __init__(self, stepper, **kwargs):
        super().__init__(**kwargs)
        self.stepper = stepper
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # Status indicator
        self.status_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.status_indicator = Label(
            text='STOPPED',
            font_size='20sp',
            color=(1, 0.3, 0.3, 1),
            bold=True
        )
        self.status_layout.add_widget(Label(text='Status:', font_size='18sp', color=(0.8, 0.8, 0.8, 1)))
        self.status_layout.add_widget(self.status_indicator)
        self.add_widget(self.status_layout)

        # Control buttons
        self.control_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15))

        self.start_btn = Button(
            text='START',
            background_color=(0.2, 0.7, 0.2, 1),
            font_size='18sp',
            bold=True
        )
        self.start_btn.bind(on_press=self.start_motor)

        self.stop_btn = Button(
            text='STOP',
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='18sp',
            bold=True
        )
        self.stop_btn.bind(on_press=self.stop_motor)

        self.control_layout.add_widget(self.start_btn)
        self.control_layout.add_widget(self.stop_btn)
        self.add_widget(self.control_layout)

        # RPM Control
        self.rpm_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        self.rpm_label = Label(
            text=f'RPM: {self.stepper.get_rpm():.1f}',
            font_size='18sp',
            color=(0.8, 0.8, 0.8, 1)
        )
        self.rpm_slider = Slider(
            min=1,
            max=200,
            value=self.stepper.get_rpm(),
            step=1,
            value_track=True,
            value_track_color=(0.2, 0.5, 0.8, 1)
        )
        self.rpm_slider.bind(value=self.update_rpm)

        self.rpm_layout.add_widget(self.rpm_label)
        self.rpm_layout.add_widget(self.rpm_slider)
        self.add_widget(self.rpm_layout)

        # Direction Control
        self.dir_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.15))
        self.dir_label = Label(
            text='DIRECTION',
            font_size='18sp',
            color=(0.8, 0.8, 0.8, 1)
        )

        self.dir_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.7))

        self.cw_btn = ToggleButton(
            text='CLOCKWISE',
            group='direction',
            state='down',
            background_color=(0.3, 0.5, 0.8, 1)
        )
        self.cw_btn.bind(on_press=lambda x: self.set_direction(True))

        self.ccw_btn = ToggleButton(
            text='COUNTER-CLOCKWISE',
            group='direction',
            background_color=(0.3, 0.5, 0.8, 1)
        )
        self.ccw_btn.bind(on_press=lambda x: self.set_direction(False))

        self.dir_buttons_layout.add_widget(self.cw_btn)
        self.dir_buttons_layout.add_widget(self.ccw_btn)

        self.dir_layout.add_widget(self.dir_label)
        self.dir_layout.add_widget(self.dir_buttons_layout)
        self.add_widget(self.dir_layout)

        # Initialize state
        self.motor_running = False
        self.current_direction = True  # Clockwise

    def start_motor(self, instance):
        if not self.motor_running:
            self.motor_running = True
            self.status_indicator.text = 'RUNNING'
            self.status_indicator.color = (0.3, 1, 0.3, 1)
            self.stepper.enable()
            self.stepper.set_direction(self.current_direction)
            # Start continuous rotation with high frequency updates
            Clock.schedule_interval(self.continuous_step, 0.001)  # 1ms updates for better timing

    def stop_motor(self, instance):
        if self.motor_running:
            self.motor_running = False
            self.status_indicator.text = 'STOPPED'
            self.status_indicator.color = (1, 0.3, 0.3, 1)
            Clock.unschedule(self.continuous_step)
            GPIO.output(self.stepper.PUL, GPIO.LOW)  # Ensure pulse is low when stopped

    def continuous_step(self, dt):
        """Non-blocking continuous stepping using time-based pulse generation"""
        current_time = time.time()
        self.stepper.generate_pulse(current_time)

    def update_rpm(self, instance, value):
        try:
            self.stepper.set_rpm(value)
            self.rpm_label.text = f'RPM: {value:.1f}'
        except ValueError as e:
            self.show_error("RPM Error", str(e))

    def set_direction(self, direction):
        self.current_direction = direction
        self.stepper.set_direction(direction)

    def show_error(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, color=(1, 1, 1, 1)))
        btn = Button(text='OK', size_hint=(1, 0.3), background_color=(0.8, 0.2, 0.2, 1))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


class StepperControlApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize stepper with your GPIO pins
        # Replace these pin numbers with your actual GPIO pins
        self.stepper = TB6600_Stepper(pul_pin=8, dir_pin=10, ena_pin=15)

    def build(self):
        self.title = "TB6600 Stepper Motor Controller"
        return StepperControlPanel(stepper=self.stepper)

    def on_stop(self):
        # Cleanup when app closes
        self.stepper.cleanup()


if __name__ == '__main__':
    try:
        StepperControlApp().run()
    except KeyboardInterrupt:
        print("App interrupted by user")
    except Exception as e:
        print(f"App error: {e}")
    finally:
        GPIO.cleanup()