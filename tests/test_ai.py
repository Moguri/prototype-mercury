# import pytest


def test_init_controller(ai_controller):
    # if we got here, we could successfully construct a controller
    assert ai_controller is not None


# AI still needs to be redone for new combat
# def test_decision_timeout(ai_controller, dt):
#     '''Test that the decision timer decrements and resets with updates'''
#     assert ai_controller.decision_timeout == 0

#     # update while decision_timeout is <= 0 should reset
#     ai_controller.update(dt)
#     assert ai_controller.decision_timeout != 0

#     # update should decrement decision_timeout by dt
#     timeout = ai_controller.decision_timeout
#     ai_controller.update(dt)
#     assert timeout - ai_controller.decision_timeout == pytest.approx(dt)
