import networkx as nx

from database import Database



class MPS(Database):

    def __init__(self, online) -> None:
        super().__init__()
        self.finished_workpieces = ('P5', 'P6', 'P7', 'P9')
        self.raw_workpieces = ('P1', 'P2')
        self.intermediate_workpieces = ('P3', 'P4', 'P8')
        self.all_pieces = self.finished_workpieces + self.raw_workpieces + self.intermediate_workpieces
        self.transformations = self.send_query("SELECT * FROM erp_mes.transformations;", fetch=True)
        self.online = online

        self.P = nx.DiGraph()
        self.P.add_nodes_from(
            self.finished_workpieces + self.raw_workpieces + self.intermediate_workpieces
        )
        self.P.add_edges_from(
            [(t[0], t[1]) for t in self.transformations]
        )


    def create_mps(self, today):
        today_orders = self.get_orders(today)
        
        stock_finished, stock_raw = self.get_stock()
        
        expedition_orders, stock_finished_updated = self.expedition_orders(
            stock_finished, 
            today_orders, 
            today
        )

        next_open_orders = self.get_next_orders(today)

        quantity_needed_finished = self.get_quantity_needed_finished(
            today_orders, 
            next_open_orders, 
            expedition_orders, 
            today
        )

        production_orders, stock_raw_updated, production_raw_material = self.production_orders(
            today_orders, 
            next_open_orders, 
            expedition_orders, 
            stock_raw,
            quantity_needed_finished,
            today
        )

        supplier_orders = self.supplier_orders(
            production_orders,
            quantity_needed_finished
        )

        if self.online is True:
            self.update_database(
                expedition_orders, 
                production_orders, 
                stock_raw_updated, 
                stock_finished_updated,
                supplier_orders
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

        stock_finished_updated = [
            tuple([
                s[1] + 1,
                s[2],
                s[3] - o[2]
            ])
            for s in stock_finished
            for o in expedition_orders
            if s[2] == o[1]
        ]

        return expedition_orders, stock_finished_updated


    def get_next_orders(self, today):
        # TODO: get orders' status.
        parameter = today + 1
        query = """SELECT * from erp_mes.client_order as o WHERE o.duedate >= (%s);"""
        return self.send_query(query, parameters=(parameter,), fetch=True)
    

    def production_orders(self, today_orders, next_open_orders, expedition_orders, stock_raw, quantity_needed_finished, today):
        # TODO: for each piece, there can't be more than one production order sent, 
        # independently of the production order day.
        # TODO: Max of 12 pieces produced on each day simultaneously.
        best_full_paths = {}

        for order in quantity_needed_finished:
            for piece in self.raw_workpieces:
                try:
                    best_full_paths[order[0]] = nx.dijkstra_path(self.P, source=piece, target=order[1])
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
                    production_raw_material = []

                    for stock in stock_raw:
                        for piece in reversed(path):
                            if piece == stock[2]:
                                stock_consumption = min(
                                    quantity_produced,
                                    stock_raw[stock_raw==stock][3]
                                )

                                stock_raw_updated.append(tuple([
                                    stock[1] + 1,
                                    stock[2],
                                    stock[3] - stock_consumption
                                ]))

                                production_raw_material.append(tuple([
                                    stock[0],
                                    stock[1],
                                    stock[2],
                                    stock_consumption
                                ]))

                                quantity_produced -= stock_consumption

        for stock in stock_raw:
            if stock[2] not in [s[1] for s in stock_raw_updated]:
                stock_raw_updated.append(
                    tuple([
                        stock[1] + 1,
                        stock[2],
                        stock[3],
                    ])
                )

        stock_raw_updated = [s for s in stock_raw_updated if s[2] > 0]

        return production_orders, stock_raw_updated, production_raw_material


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
    

    def supplier_orders(self, production_orders, quantity_needed_finished):
        # TODO: consider supplier delivery time
        lack_production = [
            tuple([
                o[0],
                o[1],
                f[2] - o[2],
                o[3]
            ]) 
            for o in production_orders
            for f in quantity_needed_finished
            if o[0] == f[0]
        ]

        supplier_orders = []

        for order in lack_production:
            raw_piece = [raw for raw in nx.ancestors(self.P, order[1]) if self.P.in_degree(raw) == 0][0]

            supplier_orders.append(
                tuple([
                    order[0],
                    raw_piece,
                    order[2],
                    order[3]
                ])
            )

        return supplier_orders


    def update_database(
            self, 
            expedition_orders, 
            production_orders, 
            stock_raw_updated,
            stock_finished_updated,
            supplier_orders
    ) -> None:
        # TODO: don't update any stock. It's up to MES.
        print("Updating Database...")

        for order in expedition_orders:
            update_expedition = """INSERT INTO erp_mes.expedition_order(
            client_order_id, piece, quantity, expedition_date
            ) VALUES (%s, %s, %s, %s)"""
            self.send_query(update_expedition, parameters=(order))

        for order in production_orders:
            update_production = """INSERT INTO erp_mes.production_order(
            client_order_id, piece, quantity, start_date
            ) VALUES (%s, %s, %s, %s)"""
            self.send_query(update_production, parameters=order)

        for stock in stock_raw_updated + stock_finished_updated:
            update_stock = """INSERT INTO erp_mes.stock(
            day, piece, quantity
            ) VALUES (%s, %s, %s)"""
            self.send_query(update_stock, parameters=stock)

        for order in supplier_orders:
            update_supply = """INSERT INTO erp_mes.supply_order(
            client_order_id, piece, quantity, buy_date
            ) VALUES (%s, %s, %s, %s)"""
            self.send_query(update_supply, parameters=order)


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