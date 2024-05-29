from database import Database



class MES(Database):
    def __init__(self):
        super().__init__()

    def is_online(self, today):
        query = "SELECT day FROM erp_mes.initial_time;"
        ans = self.send_query(query, fetch=True)
        if today == ans[0][0]:
            return True
        else:
            return False