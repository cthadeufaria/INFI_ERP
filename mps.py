from collections import defaultdict

from database import Database



class MPS(Database):

    def __init__(self) -> None:
        super().__init__()
        self.finished_workpieces = ('P5', 'P6', 'P7', 'P9')
        self.raw_workpieces = ('P1', 'P2')
        self.intermediate_workpieces = ('P3', 'P4', 'P8')


    def create_mps(self, today):
        today_orders = self.get_orders(today)
        
        stock_finished, stock_raw = self.get_stock()
        
        expedition_orders = self.expedition_orders( # TODO: insert into table expedition_order
            stock_finished, 
            today_orders, 
            today
        )

        next_open_orders = self.get_next_orders(today)

        production_orders = self.production_orders(
            today_orders, 
            next_open_orders, 
            expedition_orders, 
            stock_raw,
            today
        )

        demand = self.demand(
            next_open_orders, 
            today_orders, 
            expedition_orders, 
            production_orders
        )

        self.create_production_plan(demand)

        self.create_purchasing_plan(demand)

        self.update_stock()


    def get_orders(self, today):
        # TODO: get orders' status.
        query = """SELECT * from erp_mes.client_order as o WHERE o.duedate = (%s);"""
        return self.send_query(query, parameters=(today,), fetch=True)


    def get_stock(self):
        query = """SELECT * FROM erp_mes.stock as s
            WHERE s.day = (SELECT MAX(s1.day) from erp_mes.stock as s1);"""

        all_stock = self.send_query(query, fetch=True)

        stock_finished = [
            tpl 
            for tpl in all_stock 
            if tpl[2] in self.finished_workpieces
        ]

        stock_raw = [
            tpl 
            for tpl in all_stock 
            if (tpl[2] in self.raw_workpieces or tpl[2] in self.intermediate_workpieces)
        ]

        return stock_finished, stock_raw
        

    def expedition_orders(self, stock_finished, today_orders, today):
        # TODO: adapt code to admit more than one order of same piece per day. 
        # Subtract first order quantity from stock before calculating min().
        return [
            (
                t[0], 
                t[7], 
                min(s[3], t[3]), 
                today
            )
            for t in today_orders
            for s in stock_finished
            if s[2] == t[7]
        ]


    def get_next_orders(self, today):
        # TODO: get orders' status.
        # TODO: arbitrate until what due date ahead orders must be considered.
        parameter = today + 1
        query = """SELECT * from erp_mes.client_order as o WHERE o.duedate >= (%s);"""
        return self.send_query(query, parameters=(parameter,), fetch=True)
    

    def production_orders(self, today_orders, next_open_orders, expedition_orders, stock_raw, today):
        # TODO: Calculate how many pieces in stock_raw are needed 
        # to produce the quantity needed and return actual orders
        orders_by_date = [
            (
                order[0], 
                order[7], 
                order[3], 
                today
            )
            for order in list(today_orders + next_open_orders)
        ]

        # total_orders = {}
        
        # for order in orders_by_date:
        #     if order[1] in total_orders.keys():
        #         total_orders[order[1]] += order[2]
        #     else:
        #         total_orders[order[1]] = order[2]

        # quantity_needed = total_orders.copy()

        # for order in expedition_orders:
        #     if order[1] in quantity_needed.keys():
        #         quantity_needed[order[1]] -= order[2]

        transformations = self.send_query("SELECT * FROM erp_mes.transformations;", fetch=True)

        production_orders = {}

        for k, v in orders_by_date.items():
            production_orders[k] = v

        a = [
            (
                t[0],
                t[7], 
                min((t[3] + n[3]) - e[2], s[3]), 
                today
            )
            for t in today_orders
            for s in stock_raw
            for e in expedition_orders
            for n in next_open_orders
            if (s[2] == t[7] and e[1] == n[7] and n[7] == t[7])
        ] # old list

        return quantity_needed


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