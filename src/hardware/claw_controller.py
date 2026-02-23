# src/hardware/claw_controller.py
from loguru import logger
import time

try:
    import Jetson.GPIO as GPIO
except ImportError:
    logger.warning("Jetson.GPIO not found, running in MOCK mode")
    GPIO = None

class ClawController:
    # Pin definitions (Adjust based on wiring)
    # Using simple BCM numbering or Board numbering
    SERVO_PIN = 33 # PWM capable pin on Jetson Nano header (PWM0)

    def __init__(self):
        self.state = "UNKNOWN"
        self.mock = GPIO is None
        self.pwm = None

    def init_gpio(self):
        if self.mock:
            logger.info("Hardware initialized (MOCK)")
            return

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.SERVO_PIN, GPIO.OUT, initial=GPIO.HIGH)
        # Setup PWM
        self.pwm = GPIO.PWM(self.SERVO_PIN, 50) # 50Hz for servos
        self.pwm.start(0)
        logger.info("Hardware initialized (GPIO)")

    def open_claw(self):
        logger.info("Opening Claw...")
        if not self.mock and self.pwm:
            # Duty cycle for open (approx 2.5% to 12.5%)
            # These values need calibration for specific servo
            self.pwm.ChangeDutyCycle(7.5) 
            time.sleep(1)
            self.pwm.ChangeDutyCycle(0) # Stop jitter
        
        self.state = "OPEN"
        return "Claw is now OPEN"

    def close_claw(self):
        logger.info("Closing Claw...")
        if not self.mock and self.pwm:
            self.pwm.ChangeDutyCycle(2.5) 
            time.sleep(1)
            self.pwm.ChangeDutyCycle(0) 
        
        self.state = "CLOSED"
        return "Claw is now CLOSED"

    def get_status(self):
        return self.state

    def cleanup(self):
        if not self.mock:
            if self.pwm:
                self.pwm.stop()
            GPIO.cleanup()
        logger.info("Hardware cleanup complete")
