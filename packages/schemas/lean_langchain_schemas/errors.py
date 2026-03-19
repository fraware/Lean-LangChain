class ObligationRuntimeError(Exception):
    pass


class ParseError(ObligationRuntimeError):
    pass


class ElaborationError(ObligationRuntimeError):
    pass


class TypeMismatch(ObligationRuntimeError):
    pass


class UnknownIdentifier(ObligationRuntimeError):
    pass


class UnsolvedGoals(ObligationRuntimeError):
    pass


class ServerProtocolError(ObligationRuntimeError):
    pass


class WorkspaceConfigError(ObligationRuntimeError):
    pass


class BuildFailure(ObligationRuntimeError):
    pass


class AxiomPolicyViolation(ObligationRuntimeError):
    pass


class CheckerFailure(ObligationRuntimeError):
    pass


class Timeout(ObligationRuntimeError):
    pass


class ResourceLimit(ObligationRuntimeError):
    pass


class HumanRejected(ObligationRuntimeError):
    pass


class InternalBug(ObligationRuntimeError):
    pass
