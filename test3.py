#!/usr/bin/env python3
# two_touch_app.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.core.window import Window
from kivy.clock import Clock
import time


class TouchArea(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touches = {}  # Store active touches by touch id
        self.touch_history = []  # Store touch history

    def on_touch_down(self, touch):
        # Only process touches within this widget
        if not self.collide_point(*touch.pos):
            return False

        # Store touch information
        self.touches[touch.id] = {
            'start_pos': touch.pos,
            'current_pos': touch.pos,
            'start_time': time.time(),
            'color': self.get_touch_color(touch.id),
            'trail': [touch.pos]
        }

        print(f"Touch {touch.id} DOWN at {touch.pos}")
        self.update_display()
        return True

    def on_touch_move(self, touch):
        if touch.id in self.touches:
            self.touches[touch.id]['current_pos'] = touch.pos
            self.touches[touch.id]['trail'].append(touch.pos)

            # Keep trail manageable
            if len(self.touches[touch.id]['trail']) > 50:
                self.touches[touch.id]['trail'] = self.touches[touch.id]['trail'][-50:]

            print(f"Touch {touch.id} MOVE to {touch.pos}")
            self.update_display()
        return True

    def on_touch_up(self, touch):
        if touch.id in self.touches:
            touch_data = self.touches[touch.id]
            duration = time.time() - touch_data['start_time']

            # Add to history
            self.touch_history.append({
                'id': touch.id,
                'start_pos': touch_data['start_pos'],
                'end_pos': touch.pos,
                'duration': duration,
                'color': touch_data['color']
            })

            # Keep history manageable
            if len(self.touch_history) > 10:
                self.touch_history = self.touch_history[-10:]

            del self.touches[touch.id]
            print(f"Touch {touch.id} UP after {duration:.2f} seconds")
            self.update_display()
        return True

    def get_touch_color(self, touch_id):
        # Assign different colors to different touch IDs
        colors = [
            (1, 0, 0, 1),  # Red - Touch 1
            (0, 1, 0, 1),  # Green - Touch 2
            (0, 0, 1, 1),  # Blue - Touch 3
            (1, 1, 0, 1),  # Yellow - Touch 4
        ]
        return colors[touch_id % len(colors)]

    def update_display(self):
        self.canvas.clear()

        with self.canvas:
            # Draw touch trails for active touches
            for touch_id, touch_data in self.touches.items():
                Color(*touch_data['color'])

                # Draw trail
                if len(touch_data['trail']) > 1:
                    Line(points=[pos for pos in touch_data['trail']], width=3)

                # Draw current position
                Ellipse(pos=(touch_data['current_pos'][0] - 25,
                             touch_data['current_pos'][1] - 25), size=(50, 50))

                # Draw touch ID
                Color(1, 1, 1, 1)
                Ellipse(pos=(touch_data['current_pos'][0] - 10,
                             touch_data['current_pos'][1] - 10), size=(20, 20))


class TwoTouchApp(App):
    def build(self):
        # Set up window for Raspberry Pi Touch Display 2
        Window.fullscreen = 'auto'

        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Info panel
        info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))

        self.touch1_label = Label(text='Touch 1: Waiting', font_size='20sp')
        self.touch2_label = Label(text='Touch 2: Waiting', font_size='20sp')
        self.status_label = Label(text='Touch the screen with two fingers', font_size='20sp')

        info_layout.add_widget(self.touch1_label)
        info_layout.add_widget(self.status_label)
        info_layout.add_widget(self.touch2_label)

        # Touch area
        self.touch_area = TouchArea()

        main_layout.add_widget(info_layout)
        main_layout.add_widget(self.touch_area)

        # Update display periodically
        Clock.schedule_interval(self.update_info, 0.1)

        return main_layout

    def update_info(self, dt):
        active_touches = len(self.touch_area.touches)

        # Update touch status labels
        touch_texts = ['Waiting'] * 2
        for i, touch_id in enumerate(list(self.touch_area.touches.keys())[:2]):
            touch_data = self.touch_area.touches[touch_id]
            pos = touch_data['current_pos']
            touch_texts[i] = f"Touch {touch_id + 1}: ({int(pos[0])}, {int(pos[1])})"

        self.touch1_label.text = touch_texts[0] if len(touch_texts) > 0 else 'Touch 1: Waiting'
        self.touch2_label.text = touch_texts[1] if len(touch_texts) > 1 else 'Touch 2: Waiting'

        # Update status
        if active_touches == 0:
            self.status_label.text = 'No active touches'
        elif active_touches == 1:
            self.status_label.text = '1 touch active - add another finger'
        else:
            self.status_label.text = f'{active_touches} touches active'


if __name__ == '__main__':
    TwoTouchApp().run()