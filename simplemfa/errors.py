from simplemfa.constants import MessageConstants


class MFACodeNotSentError(Exception):

    def __init__(self, message=MessageConstants.MFA_GENERIC_ERROR):
        self.message = message
        super().__init__(self.message)


class MFACodeNotCreatedError(MFACodeNotSentError):

    def __init__(self, message=MessageConstants.MFA_GENERIC_ERROR):
        super(MFACodeNotCreatedError, self).__init__(message)