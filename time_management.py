


class Clock:
    def __init__(self) -> None:
        pass


    def listen(self):
        self.trigger = True
        self.today = self.get_day()


    def get_day(self):
        return 4