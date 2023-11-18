class MinerPyError(Exception):
    pass


class TryNotFoundException(MinerPyError):
    pass


class ExceptClauseExpectedException(MinerPyError):
    pass


class FunctionDefNotFoundException(MinerPyError):
    pass


class TreeSitterNodeException(MinerPyError):
    pass


class CallGraphError(MinerPyError):
    pass
