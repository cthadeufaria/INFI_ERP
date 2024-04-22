from database import Database



class MPS:

    def __init__(self) -> None:
        self.db = Database()


    def create_mps(self, today):
        today_orders = self.get_orders(today)
        
        stock_finished, stock_raw = self.get_stock()
        
        expedition_orders = self.expedition_orders(stock_finished, today_orders)

        next_open_orders = self.get_next_orders()

        production_orders = self.production_orders(today_orders, next_open_orders, expedition_orders, stock_raw)

        demand = self.demand(next_open_orders, today_orders, expedition_orders, production_orders)

        self.create_production_plan(demand)

        self.create_purchasing_plan(demand)

        self.update_stock()


    def get_orders(self, today):
        # TODO: get orders' status
        query = """SELECT * from "INFI".orders as o WHERE o.duedate = (%s);"""
        return self.db.send_query(query, parameters=(today,), fetch=True)


    def get_stock(self):
        query = """SELECT * FROM "INFI".stock as s
            WHERE s.day = (SELECT MAX(s1.day) from "INFI".stock as s1);"""

        all_stock = self.db.send_query(query, fetch=True)

        finished_workpieces = ('P5', 'P6', 'P7', 'P9')
        raw_workpieces = ('P1', 'P2')
        intermediate_workpieces = ('P3', 'P4', 'P8')

        stock_finished = [tpl for tpl in all_stock if tpl[2] in finished_workpieces]
        stock_raw = [
            tpl for tpl in all_stock if (tpl[2] in raw_workpieces or tpl[2] in intermediate_workpieces)
        ]

        return stock_finished, stock_raw
        

    def expedition_orders(self, stock_finished, today_orders):
        return min(stock_finished, today_orders)


    def get_next_orders(self):
        # TODO get orders for next days
        pass


    def production_orders(self, today_orders, next_open_orders, expedition_orders, stock_raw):
        return min((today_orders + next_open_orders) - expedition_orders, stock_raw)


    def demand(self, next_open_orders, today_orders, expedition_orders, production_orders):
        return next_open_orders + today_orders - expedition_orders - production_orders


    def create_production_plan(self, demand):
        pass


    def create_purchasing_plan(self, demand):
        pass


    def update_stock(self):
        pass


    def total_cost(self, Rc, Pc, Dc):
        return Rc + Pc + Dc
    

    def depreciation_cost(self, Rc, Dd, Ad):
        return Rc * (Dd - Ad) * 0.01
    

    def production_cost(self, Pt):
        return 1 * Pt
    
    
# Tc = Rc + Pc + Dc
# Tc – Total Cost
# Rc – Raw Material Cost (price of the raw material used to produce that piece)
# Pc – Production Cost (Cost to Produce the piece)
# Dc – Depreciation Cost (Cost of money invested in the piece)
# Dc = Rc x (Dd - Ad) x 1%
# Ad – Arrival Date – date the raw material arrived at the production line
# Dd – Dispatch Date – date final work-piece leaves the production line (unloaded on cell E)
# Pc = € 1 x Pt
# Pt – Total Production time (in seconds).