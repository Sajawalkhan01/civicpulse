from .enums import Status

TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS, Status.REJECTED}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED, Status.REJECTED}),
    Status.RESOLVED: frozenset(),
    Status.REJECTED: frozenset(),
}


class InvalidTransitionError(Exception):
    def __init__(self, current: Status, target: Status) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition complaint from {current.value!r} to {target.value!r}"
        )


def can_transition(current: Status, target: Status) -> bool:
    return target in TRANSITIONS[current]


def validate_transition(current: Status, target: Status) -> None:
    if not can_transition(current, target):
        raise InvalidTransitionError(current, target)
