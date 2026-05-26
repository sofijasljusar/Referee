class InvalidPayingStateError(Exception):
    pass

class EmptyGroupError(Exception):
    pass

class GroupCodeGenerationError(Exception):
    pass

class GroupClosed(Exception):
    pass

class MemberLeft(Exception):
    pass
