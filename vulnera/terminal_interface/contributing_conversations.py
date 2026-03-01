"""
Contribution features were removed as part of the rebranding.

The original module allowed users to contribute past and future conversations
to a hosted Open Interpreter training endpoint and provided interactive
prompts. That functionality has been disabled to remove Open Interpreter's
hosted model integration and external endpoints.

The public API of this module remains (no-op) to avoid requiring edits
in callers. All functions below are intentionally inert.
"""

def display_contribution_message():
    # previously showed prompts to contribute conversations; removed
    return None


def display_contributing_current_message():
    return None


def send_past_conversations(vulnera):
    # contribution disabled
    return None


def set_send_future_conversations(vulnera, should_send_future):
    # contribution disabled
    return None


def user_wants_to_contribute_past():
    return False


def user_wants_to_contribute_future():
    return False


def contribute_conversation_launch_logic(vulnera):
    # no-op launch logic
    return None


def contribute_conversations(conversations, feedback=None, conversation_id=None):
    # contributions removed
    return None
