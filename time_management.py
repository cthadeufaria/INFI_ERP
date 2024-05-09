from datetime import datetime as dt

from database import Database


class Clock(Database):
    def __init__(self, debug) -> None:
        super().__init__()
        self.get_initial_time()
        self.reset_trigger()
        self.yesterday = 0
        self.debug = debug


    def listen(self):
        while True:
            if self.debug is False:
                self.today = int((dt.now() - self.initial_time).total_seconds() / 60)
            elif self.debug is True:
                self.today = 4
            if self.today > self.yesterday:
                print("Today is ", self.today)
                self.trigger = True
                self.yesterday = self.today


    def get_day(self):
        return 4
    

    def get_initial_time(self):
        self.initial_time = self.send_query(
            "SELECT initial_time from erp_mes.start_time;",
            fetch=True
        )[0][0]

    
    def reset_trigger(self):
        self.trigger = False