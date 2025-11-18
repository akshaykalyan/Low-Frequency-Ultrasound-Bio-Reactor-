#define dirPin 2
#define stepPin 3

void setup() {
  // Declare pins as output:
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  // Set the spinning direction CW/CCW:
  digitalWrite(dirPin, HIGH);
}

void loop() {
  // These four lines result in 1 step:
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(800);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(800);
}