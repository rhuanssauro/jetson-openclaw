from hardware.claw_controller import ClawController


def test_claw_controller_init():
    claw = ClawController()
    claw.init_gpio()
    assert claw.get_status() == "UNKNOWN"


def test_claw_open():
    claw = ClawController()
    claw.init_gpio()

    response = claw.open_claw()
    assert response == "Claw is now OPEN"
    assert claw.get_status() == "OPEN"


def test_claw_close():
    claw = ClawController()
    claw.init_gpio()

    response = claw.close_claw()
    assert response == "Claw is now CLOSED"
    assert claw.get_status() == "CLOSED"
