from datetime import datetime as dt, timedelta

from database import Database


class Clock(Database):
    def __init__(self, debug) -> None:
        super().__init__()
        self.get_initial_time(debug)
        self.reset_trigger()
        self.yesterday = 0
        self.debug = debug


    def listen(self):
        while True:
            self.today = int((dt.now() - self.initial_time).total_seconds() / 60)
            if self.today > self.yesterday:
                print("Today is ", self.today)
                self.trigger = True
                self.yesterday = self.today
    

    def get_initial_time(self, debug):
        if debug is False:
            self.initial_time = self.send_query(
                "SELECT initial_time from erp_mes.start_time;",
                fetch=True
            )[0][0]
        elif debug is True:
            self.initial_time = dt.now() - timedelta(seconds=300)

    
    def reset_trigger(self):
        self.trigger = False