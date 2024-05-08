import networkx as nx

from database import Database



class MPS(Database):

    def __init__(self) -> None:
        super().__init__()
        self.finished_workpieces = ('P5', 'P6', 'P7', 'P9')
        self.raw_workpieces = ('P1', 'P2')
        self.intermediate_workpieces = ('P3', 'P4', 'P8')
        self.all_pieces = self.finished_workpieces + self.raw_workpieces + self.intermediate_workpieces


    def create_mps(self, today):
        today_orders = self.get_orders(today)
        
        stock_finished, stock_raw = self.get_stock()
        
        expedition_orders, stock_finished_updated = self.expedition_orders(
            stock_finished, 
            today_orders, 
            today
        )

        next_open_orders = self.get_next_orders(today)

        production_orders, stock_raw_updated = self.production_orders(
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

        self.update_database(
            expedition_orders, 
            production_orders, 
            stock_raw_updated, 
            stock_finished_updated
        )


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
        # TODO: update stock finished
        expedition_orders = [
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

        stock_finished_updated = []

        return expedition_orders, stock_finished_updated


    def get_next_orders(self, today):
        # TODO: get orders' status.
        # TODO: arbitrate until what due date ahead orders must be considered.
        parameter = today + 1
        query = """SELECT * from erp_mes.client_order as o WHERE o.duedate >= (%s);"""
        return self.send_query(query, parameters=(parameter,), fetch=True)
    

    def production_orders(self, today_orders, next_open_orders, expedition_orders, stock_raw, today):
        quantity_needed_finished = self.get_quantity_needed_finished(today_orders, next_open_orders, expedition_orders, today)

        transformations = self.send_query("SELECT * FROM erp_mes.transformations;", fetch=True)

        P = nx.DiGraph()
        P.add_nodes_from(
            self.finished_workpieces + self.raw_workpieces + self.intermediate_workpieces
        )
        P.add_edges_from(
            [(t[0], t[1]) for t in transformations]
        )

        best_full_paths = {}

        for order in quantity_needed_finished:
            for piece in self.raw_workpieces:
                try:
                    best_full_paths[order[0]] = nx.dijkstra_path(P, source=piece, target=order[1])
                except nx.exception.NetworkXNoPath:
                    pass

        production_orders = []

        for order in quantity_needed_finished:
            for order_id, path in best_full_paths.items():
                if order_id == order[0]:
                    quantity_produced = min(
                                order[2],
                                sum([s[3] for s in stock_raw if s[2] in path])
                            )
                    production_orders.append(
                        tuple([
                            order[0],
                            order[1],
                            quantity_produced,
                            today
                        ])
                    )

                    stock_raw_updated = []

                    for stock in stock_raw:
                        for piece in reversed(path):
                            if piece == stock[2]:
                                stock_consumption = min(
                                    quantity_produced,
                                    stock_raw[stock_raw==stock][3]
                                )
                                stock_raw_updated.append(tuple([
                                    stock[0],
                                    stock[1],
                                    stock[2],
                                    stock[3] - stock_consumption
                                ]))
                                quantity_produced -= stock_consumption

        for stock in stock_raw:
            print(stock)
            print(stock_raw_updated)
            if stock[2] not in [s[2] for s in stock_raw_updated]:
                stock_raw_updated.append(stock)

        return production_orders, stock_raw_updated


    def get_quantity_needed_finished(self, today_orders, next_open_orders, expedition_orders, today):
        orders_by_date = [
            (
                order[0], 
                order[7], 
                order[3], 
                today
            )
            for order in list(today_orders + next_open_orders)
        ]

        quantity_needed = orders_by_date.copy()
        
        for expedition_order in expedition_orders:
            for order in orders_by_date:
                if expedition_order[1] == order[1] and expedition_order[1] == order[1]:                    
                    quantity_needed[
                        quantity_needed == order
                    ] = tuple(
                        [
                            order[0], 
                            order[1], 
                            order[2] - 
                            expedition_order[2], 
                            order[3]
                        ]
                    )

        return [t for t in quantity_needed if t[2] > 0]
    

    def demand(self, next_open_orders, today_orders, expedition_orders, production_orders):
        return next_open_orders + today_orders - expedition_orders - production_orders


    def create_production_plan(self, demand):
        pass


    def create_purchasing_plan(self, demand):
        pass


    def update_database(self):
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