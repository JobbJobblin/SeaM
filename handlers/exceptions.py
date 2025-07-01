class empty_from_e(Exception):
    def __init__(self, msg :str = "No files found in FROM directory") -> None:
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return f'{self.msg}'

class rollback_e(Exception):
    def __init__(self, msg :str = "Rollback from recurring function") -> None:
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return f'{self.msg}'
