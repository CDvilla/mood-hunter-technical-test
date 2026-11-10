ALLOWED_STATUS_TRANSITIONS = {
    "created": frozenset({"in_review"}),
    "in_review": frozenset({"in_progress", "paused"}),
    "in_progress": frozenset({"done", "paused"}),
    "paused": frozenset({"in_progress", "in_review"}),
    "done": frozenset(),
}


class InvalidRequestStatusTransition(ValueError):
    pass


def validate_request_status_transition(current_status: str, next_status: str) -> None:
    if next_status not in ALLOWED_STATUS_TRANSITIONS.get(current_status, ()):
        raise InvalidRequestStatusTransition(
            f"Cannot transition a request from '{current_status}' "
            f"to '{next_status}'."
        )
