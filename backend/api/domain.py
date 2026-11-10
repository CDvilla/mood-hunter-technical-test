from api.models import Request


ALLOWED_STATUS_TRANSITIONS = {
    Request.Status.CREATED: frozenset({Request.Status.IN_REVIEW}),
    Request.Status.IN_REVIEW: frozenset(
        {Request.Status.IN_PROGRESS, Request.Status.PAUSED}
    ),
    Request.Status.IN_PROGRESS: frozenset(
        {Request.Status.DONE, Request.Status.PAUSED}
    ),
    Request.Status.PAUSED: frozenset(
        {Request.Status.IN_PROGRESS, Request.Status.IN_REVIEW}
    ),
    Request.Status.DONE: frozenset(),
}


class InvalidRequestStatusTransition(ValueError):
    pass


def validate_request_status_transition(current_status, next_status):
    if next_status not in ALLOWED_STATUS_TRANSITIONS.get(current_status, ()):
        raise InvalidRequestStatusTransition(
            f"Cannot transition a request from '{current_status}' "
            f"to '{next_status}'."
        )
