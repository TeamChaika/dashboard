class RequestFailed(Exception):
    def __init__(self, status: int, message: str, *args: object) -> None:
        self.message = f'{status}: {message}'
        super().__init__(self.message, *args)
