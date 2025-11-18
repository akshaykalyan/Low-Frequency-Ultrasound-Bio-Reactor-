import RPi.GPIO as GPIO
import time

class TB6600_Stepper:
    def __init__(self, pul_pin, dir_pin, ena_pin=None):
        self.PUL = pul_pin
        self.DIR = dir_pin
        self.ENA = ena_pin

        self.steps_per_rev = 200
        self.microsteps = 1
        self.delay = 0.005

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
        self.delay = (rpm/60) / self.microsteps
    def get_rpm(self):
        return self.delay * self.microsteps *60

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

    def cleanup(self):
        self.disable()
        GPIO.cleanup()
        print("GPIO cleanup completed")



stepper = TB6600_Stepper(pul_pin=8, dir_pin=10, ena_pin=13)

stepper.set_rpm(60)
print("Test 1: 100 steps forward")
stepper.step(200)
time.sleep(1)
stepper.set_rpm(30)
print(stepper.get_rpm())
print("Test 2: 100 steps backward")
stepper.step(-200)
time.sleep(1)

print("Test 3: 90 degree rotation")
stepper.rotate_degrees(360, direction=True)

