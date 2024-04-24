import datetime


class NeverExpires:
    def expired(self):
        return False


class Timer:
    """
    A simple timer that will indicate when an expiration time has passed.
    """

    def __init__(self, expiration):
        self.expiration = expiration

    @classmethod
    def after(cls, elapsed):
        """
        Return a timer that will expire after `elapsed` passes.
        """
        return cls(datetime.datetime.utcnow() + elapsed)

    def expired(self):
        return datetime.datetime.utcnow() >= self.expiration
