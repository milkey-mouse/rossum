//Ctrl-Q to upload

#include <Servo.h>

Servo pan;
Servo tilt;
Servo leftWheel;
Servo rightWheel;

bool shutdown = false;

void setup() {
    pan.attach(9);
    pan.write(50);
    tilt.attach(10);
    for (int pos = 42; pos <= 120; pos++) {
        tilt.write(pos);
        delay(25);
    }
    pan.detach();
    tilt.detach();
    pinMode(4, INPUT_PULLUP);
    Serial.begin(19200);
}

void toggleCamera() {
    tilt.attach(10);
        if(shutdown) {
            for (int pos = 42; pos <= 120; pos++) {
                tilt.write(pos);
                delay(25);
            }
        }
        else
        {
            for (int pos = 120; pos >= 42; pos--) {
                tilt.write(pos);
                delay(25);
            }
        }
        tilt.detach();
        shutdown = !shutdown;
}

void loop() {
    if(digitalRead(4) == LOW)
    {
        toggleCamera();
    }
}

void serialEvent() {
    int cmdChar = Serial.read();
    if(cmdChar == 'S') {
        toggleCamera();
        return;
    }
    else if(cmdChar == 'H') {
        if(leftWheel.attached()) {
            leftWheel.detach();
        }
        if(rightWheel.attached()) {
            rightWheel.detach();
        }
        return;
    }
    int servoMicroseconds = Serial.parseInt();
    if(cmdChar == 'L') {
        if(servoMicroseconds == 1500) {
            if(leftWheel.attached()) {
                leftWheel.detach();
            }
        }
        else {
            if(!leftWheel.attached()) {
                leftWheel.attach(12);
            }
            leftWheel.writeMicroseconds(servoMicroseconds);
        }
    }
    else if(cmdChar == 'R') {
        if(servoMicroseconds == 1500) {
            if(rightWheel.attached()) {
                rightWheel.detach();
            }
        }
        else {
            if(!rightWheel.attached()) {
                rightWheel.attach(11);
            }
            rightWheel.writeMicroseconds(servoMicroseconds);
        }
    }
}
