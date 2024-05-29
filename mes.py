from database import Database



class MES(Database):
    def __init__(self, debug):
        super().__init__()
        self.debug = debug

    def is_online(self, today):
        query = "SELECT day FROM erp_mes.start_time;"
        ans = self.send_query(query, fetch=True)
        
        if ans == []:
            mes_day = 0
        else:
            mes_day = ans[0][0]

        if today == mes_day or self.debug == True:
            return True
        else:
            return False