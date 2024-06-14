import networkx as nx

from database import Database



class MPS(Database):

    def __init__(self, debug) -> None:
        super().__init__()
        self.finished_workpieces = ('P5', 'P6', 'P7', 'P9')
        self.raw_workpieces = ('P1', 'P2')
        self.intermediate_workpieces = ('P3', 'P4', 'P8')
        self.all_pieces = self.finished_workpieces + self.raw_workpieces + self.intermediate_workpieces
        self.transformations = self.send_query("SELECT * FROM erp_mes.transformations;", fetch=True)
        self.debug = debug

        self.P = nx.DiGraph()
        self.P.add_nodes_from(
            self.finished_workpieces + self.raw_workpieces + self.intermediate_workpieces
        )
        self.P.add_edges_from(
            [(t[0], t[1]) for t in self.transformations]
        )

        self.last_deliveries = [0, 0, 0]


    def create_mps(self, today):
        today_orders = self.get_orders(today)
        
        stock_finished, stock_raw = self.get_stock()
        
        expedition_orders, stock_finished_updated = self.expedition_orders(
            stock_finished, 
            today_orders, 
            today
        )

        next_open_orders = self.get_next_orders(today)

        last_production_orders = self.get_last_production_orders(today)

        quantity_needed_finished = self.get_quantity_needed_finished(
            today_orders, 
            next_open_orders, 
            expedition_orders,
            last_production_orders,
            today
        )
        
        production_orders, production_orders_capacity, stock_raw_updated, production_raw_material = self.production_orders(
            today_orders, 
            next_open_orders, 
            expedition_orders, 
            stock_raw,
            quantity_needed_finished,
            today
        )

        supplier_needs = self.supplier_needs(
            production_orders_capacity,
            quantity_needed_finished
        )

        supplier_orders, stock_raw_updated_2, new_deliveries = self.supplier_orders(
            supplier_needs, 
            stock_raw_updated
        )

        total_costs = self.calculate_costs(today)

        if self.debug is False:
            self.update_database(
                expedition_orders, 
                production_orders, 
                stock_raw_updated_2, 
                stock_finished_updated,
                supplier_orders,
                new_deliveries,
                production_raw_material,
                total_costs
            )
            
        print("today_orders:")
        print(today_orders)
        print("\n")
        print("stock_finished:")
        print(stock_finished)
        print("\n")
        print("stock_raw:")
        print(stock_raw)
        print("\n")
        print("expedition_orders:")
        print(expedition_orders)
        print("\n")
        print("stock_finished_updated:")
        print(stock_finished_updated)
        print("\n")
        print("next_open_orders:")
        print(next_open_orders)
        print("\n")
        print("last_production_orders:")
        print(last_production_orders)
        print("\n")        
        print("quantity_needed_finished:")
        print(quantity_needed_finished)
        print("\n")        
        print("production_orders:")
        print(production_orders)
        print("\n")
        print("supplier_needs:")
        print(supplier_needs)
        print("\n")        
        print("suppler_orders:")
        print(supplier_orders)
        print("\n")
        print("new_deliveries:")
        print(new_deliveries)
        print("\n")


    def get_orders(self, today):
        query = """SELECT DISTINCT
            o.id, o.client_id, o.number, o.quantity - 
            case when s.quantity is null then 0
            else s.quantity
            end,
            o.duedate, o.latepen, o.earlypen, o.piece
            from erp_mes.client_order as o 
            left outer join 
            (SELECT * 
            from erp_mes.expedition_order eo
            left outer join 
            erp_mes.expedition_status es
            on eo.id = es.expedition_order_id) s
            on o.id = s.client_order_id
            WHERE s.end_date is NULL
            AND o.duedate <= (%s)
            GROUP BY o.id, o.client_id, o.number, o.quantity - 
            case when s.quantity is null then 0
            else s.quantity
            end,
            o.duedate, o.latepen, o.earlypen, o.piece
            HAVING o.quantity - 
            case when s.quantity is null then 0
            else s.quantity
            end > 0;"""
        return self.send_query(query, parameters=(today,), fetch=True)
    

    def get_last_production_orders(self, today):
        query = """SELECT o.client_order_id, o.piece, sum(o.quantity)
                FROM erp_mes.production_order o
                WHERE o.start_date <= (%s)
                GROUP BY o.client_order_id, o.piece;"""

        return self.send_query(query, parameters=(today,), fetch=True)


    def get_stock(self):
        query = """SELECT * FROM erp_mes.stock as s
            WHERE s.day = (SELECT MAX(s1.day) from erp_mes.stock as s1);"""

        all_stock = self.send_query(query, fetch=True)

        stock_finished = [
            tpl 
            for tpl in all_stock 
            if tpl[2] in self.finished_workpieces
            and tpl[3] > 0
        ]

        stock_raw = [
            tpl 
            for tpl in all_stock 
            if (tpl[2] in self.raw_workpieces or tpl[2] in self.intermediate_workpieces)
            and tpl[3] > 0
        ]

        return stock_finished, stock_raw
        

    def expedition_orders(self, stock_finished, today_orders, today):
        # expedition_orders = [
        #     (
        #         t[0], 
        #         t[7], 
        #         min(s[3], t[3]), 
        #         today
        #     )
        #     for t in today_orders
        #     for s in stock_finished
        #     if (s[2] == t[7]) and (s[3] - t[3] >= 0)
        # ]

        stock_finished = [list(s) for s in stock_finished]

        expedition_orders = []
        for t in today_orders:
            for s in stock_finished:
                if (s[2] == t[7]) and (s[3] - t[3] >= 0):
                    expedition_orders.append((t[0], t[7], t[3], today))
                    s[3] -= t[3]

        stock_finished_updated = [tuple(s) for s in stock_finished]

        # stock_finished_updated = [
        #     tuple([
        #         s[1] + 1,
        #         s[2],
        #         s[3] - o[2]
        #     ])
        #     for s in stock_finished
        #     for o in expedition_orders
        #     if s[2] == o[1]
        # ]

        return [e for e in expedition_orders if e[2] > 0], stock_finished_updated


    def get_next_orders(self, today):
        parameter = today + 1
        query = """SELECT DISTINCT
            o.id, o.client_id, o.number, o.quantity - 
            case when s.quantity is null then 0
            else s.quantity
            end,
            o.duedate, o.latepen, o.earlypen, o.piece
            from erp_mes.client_order as o 
            left outer join 
            (SELECT * 
            from erp_mes.expedition_order eo
            left outer join 
            erp_mes.expedition_status es
            on eo.id = es.expedition_order_id) s
            on o.id = s.client_order_id
            WHERE s.end_date is NULL
            AND o.duedate >= (%s)
            GROUP BY o.id, o.client_id, o.number, o.quantity - 
            case when s.quantity is null then 0
            else s.quantity
            end,
            o.duedate, o.latepen, o.earlypen, o.piece
            HAVING o.quantity - 
            case when s.quantity is null then 0
            else s.quantity
            end > 0;"""
        return self.send_query(query, parameters=(parameter,), fetch=True)
    

    def production_orders(self, today_orders, next_open_orders, expedition_orders, stock_raw, quantity_needed_finished, today):
        best_full_paths = {}
        stock_raw_updated = stock_raw.copy()
        alternative_paths = {}

        for order in quantity_needed_finished:
            for piece in self.raw_workpieces:
                try:
                    best_full_paths[order[0]] = nx.dijkstra_path(self.P, source=piece, target=order[1])
                    if order[1] == 'P7' and piece == 'P1':
                        alternative_paths[order[0]] = nx.dijkstra_path(self.P, source=piece, target=order[1])
                except nx.exception.NetworkXNoPath:
                    pass

        production_orders = []
        production_raw_material = []

        for order_id, path in alternative_paths.items():
            best_full_paths[order_id] += path

        for order in quantity_needed_finished:
            for order_id, path in best_full_paths.items():
                if order_id == order[0]:
                    quantity_produced = min(
                                order[2],
                                sum([s[3] for s in stock_raw_updated if s[2] in path])
                            )
                    production_orders.append(
                        [
                            order[0],
                            order[1],
                            quantity_produced,
                            today
                        ]
                    )

                    i = 0

                    for stock in stock_raw_updated:
                        for piece in reversed(path):
                            if piece == stock[2]:
                                stock_consumption = min(
                                    quantity_produced,
                                    stock[3]
                                )

                                quantity_produced -= stock_consumption
                                
                                stock_raw_updated[i] = tuple([
                                    stock[0],
                                    stock[1],
                                    stock[2],
                                    stock[3] - stock_consumption
                                ])

                                # production_raw_material.append(tuple([
                                #     order[0],
                                #     stock[2],
                                #     stock_consumption,
                                #     today
                                # ]))
                        
                        i += 1

        stock_raw_updated = [s for s in stock_raw_updated if s[3] > 0]

        production_orders_final = []
        production_orders_final_capacity = production_orders.copy()
        all_pieces = 0

        for p in production_orders:
            all_pieces += p[2]
            if all_pieces <= 12:
                production_orders_final.append(
                    tuple([
                        p[0],
                        p[1],
                        p[2],
                        p[3]
                    ])
                )
            else:
                production_orders_final.append(
                    tuple([
                        p[0],
                        p[1],
                        12 - sum([f[2] for f in production_orders_final]),
                        p[3]
                    ])
                )
                break

        production_orders_final = [p for p in production_orders_final if p[2] > 0]
        production_orders_final_capacity = [
            p for p in production_orders_final_capacity if p[2] > 0
        ]

        for order in production_orders_final:
            for order_id, path in best_full_paths.items():
                if order_id == order[0]:
                    for piece in reversed(path):
                        if piece == stock[2]:
                            production_raw_material.append(tuple([
                                order[0], piece, order[2], order[3]
                            ]))

        return production_orders_final, production_orders_final_capacity, stock_raw_updated, production_raw_material


    def get_quantity_needed_finished(self, today_orders, next_open_orders, expedition_orders, last_production_orders, today):
        orders_by_date = [
            (
                order[0], 
                order[7], 
                order[3], 
                today
            )
            for order in list(today_orders + next_open_orders)
        ]

        quantity_needed = []

        if len(last_production_orders) == 0:
            quantity_needed = orders_by_date.copy()
        else:
            for production_order in last_production_orders:
                for order in orders_by_date:
                    if production_order[0] == order[0] and production_order[1] == order[1]:                 
                        quantity_needed.append(tuple(
                            [
                                order[0], 
                                order[1], 
                                order[2] - 
                                production_order[2], 
                                order[3]
                            ]
                        ))

        orders_not_produced = [o for o in orders_by_date if o[0] not in [q[0] for q in quantity_needed]]

        for order in orders_not_produced:
            quantity_needed.append(order)
        
        return [t for t in quantity_needed if t[2] > 0]
    

    def supplier_needs(self, production_orders, quantity_needed_finished):
        lack_production = []

        for o in production_orders:
            for f in quantity_needed_finished:
                if o[0] == f[0]:
                    lack_production.append(
                        tuple([
                        o[0],
                        o[1],
                        f[2] - o[2],
                        o[3]
                    ]) 
                    )

        for f in quantity_needed_finished:
            if f[0] not in [o[0] for o in production_orders]:
                lack_production.append(
                    f
                )

        lack_production = [l for l in lack_production if l[2] > 0]

        supplier_needs = []

        for order in lack_production:
            raw_piece = [raw for raw in nx.ancestors(self.P, order[1]) if self.P.in_degree(raw) == 0][0]

            supplier_needs.append(
                tuple([
                    order[0],
                    raw_piece,
                    order[2],
                    order[3]
                ])
            )

        return supplier_needs


    def get_suppliers(self):
        suppliers_query = """SELECT * from erp_mes.supplier;"""
        return self.send_query(suppliers_query, fetch=True)


    def supplier_orders(self, supplier_needs, stock_raw):
        suppliers = self.get_suppliers()

        supplier_orders = []

        # TODO: Optimize supplier selection. Not optimized. Just choosing the faster delivery.
        supplier = 'SupplierC'
        
        for order in supplier_needs:
            supplier_orders.append([
                order[0],
                order[1],
                max(
                    order[2],
                    [m[3] for m in suppliers if m[2] == order[1] and m[1] == supplier][0]
                ),
                order[3]
            ])

        stock_raw_updated_2 = []

        for stock in stock_raw:
            stock_raw_updated_2.append([
                stock[1] + 1,
                stock[2],
                stock[3]
            ])

        stock_raw_updated_suppliers = []
        for order in supplier_orders:        
            stock_raw_updated_suppliers.append([
                order[3] + [m[5] for m in suppliers if m[2] == order[1] and m[1] == supplier][0],
                order[1],
                order[2]
            ])

        if len(stock_raw_updated_suppliers) == 0:
            stock_raw_updated_suppliers_2 = stock_raw_updated_suppliers.copy()
        else:
            stock_raw_updated_suppliers_2 = [stock_raw_updated_suppliers[0]]
            for stock_1 in stock_raw_updated_suppliers[1:]:
                for stock_2 in stock_raw_updated_suppliers_2:
                    if stock_1[0] == stock_2[0] and stock_1[1] == stock_2[1]:
                        stock_raw_updated_suppliers_2[
                            stock_raw_updated_suppliers_2 == stock_1
                        ] = [stock_1[0], stock_2[1], stock_1[2] + stock_2[2]]

        if len(stock_raw_updated_2) == 0:
            stock_raw_updated_2 = stock_raw_updated_suppliers_2.copy()
        else:
            for stock_1 in stock_raw_updated_suppliers_2:
                for stock_2 in stock_raw_updated_2:
                    if stock_1[0] == stock_2[0] and stock_1[1] == stock_2[1]:
                        stock_2[2] = stock_2[2] + stock_1[2]
                    else:
                        stock_raw_updated_2.append(
                            stock_1
                        )

        stock_raw_updated_suppliers_3 = [
            [s[0], s[1], s[2] - (self.last_deliveries[1] if s[1] == 'P1' else self.last_deliveries[2])]
            for s in stock_raw_updated_suppliers_2
        ]

        if len(stock_raw_updated_suppliers_3) == 0:
            day = 0
        else:
            day = stock_raw_updated_suppliers_3[0][0]
        new_deliveries = tuple([
            day,
            sum([s[2] for s in stock_raw_updated_suppliers_3 if s[1] == 'P1']),
            sum([s[2] for s in stock_raw_updated_suppliers_3 if s[1] == 'P2'])
        ])

        self.last_deliveries = [n for n in new_deliveries]

        return supplier_orders, stock_raw_updated_2, new_deliveries


    def calculate_costs(self, today):
        """
        # Tc = Rc + Pc + Dc
        # Tc = Total Cost
        # Rc = Raw Material Cost (price of the raw material used to produce that piece)
        # Pc = Production Cost (Cost to Produce the piece)
        # Dc = Depreciation Cost (Cost of money invested in the piece)
        # Dc = Rc x (Dd - Ad) x 1%
        # Ad = Arrival Date - date the raw material arrived at the production line
        # Dd = Dispatch Date - date final work-piece leaves the production line (unloaded on cell E)
        # Pc = € 1 x Pt
        # Pt = Total Production time (in seconds).
        """

        suppliers = self.get_suppliers()
        supplier = 'SupplierC'

        individual_raw_material_cost = [
            [s[2], s[4]] for s in suppliers if s[1] == supplier
        ]

        parameter = today - 1
        # TODO: check costs query and calculation ; check correctness of production_raw_material update (why P3 instead of P1?)
        costs_query = """select 
                p.client_order_id, p.piece, p.quantity,
                es.end_date - s.buy_date + 1,
                pi.total_time
                from erp_mes.production_raw_material as p,
                erp_mes.expedition_order as eo,
                erp_mes.expedition_status as es,
                erp_mes.supply_order as s,
                erp_mes.piece_info as pi
                where p.client_order_id = s.client_order_id
                and s.client_order_id = eo.client_order_id
                and eo.client_order_id = pi.client_order_id
                and eo.id = es.expedition_order_id
                and p.client_order_id in 
                (select 
                distinct o.client_order_id 
                from erp_mes.expedition_order as o, erp_mes.expedition_status as s
                where s.end_date = (%s));"""
        costs = self.send_query(costs_query, parameters=(parameter,), fetch=True)

        total_costs = []

        costs_adapted = [list(c) for c in costs]

        for cost in costs_adapted:
            if cost[1] not in self.raw_workpieces:
                if cost[1] in ['P3', 'P4', 'P5', 'P7', 'P6']:
                    cost[1] = 'P1'
                else:
                    cost[1] = 'P2'

        for row in costs_adapted:
            total_costs.append([
                row[0],
                row[1],
                row[2],
                row[3], 
                row[2] * [r[1] for r in individual_raw_material_cost if r[0] == row[1]][0],
                row[2] * [r[1] for r in individual_raw_material_cost if r[0] == row[1]][0] * row[3] * 0.01,
                row[4]
            ])

        return total_costs
        

    def update_database(
            self, 
            expedition_orders, 
            production_orders, 
            stock_raw_updated,
            stock_finished_updated,
            supplier_orders,
            new_deliveries,
            production_raw_material,
            total_costs
    ) -> None:
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

        for order in supplier_orders:
            update_supply = """INSERT INTO erp_mes.supply_order(
            client_order_id, piece, quantity, buy_date
            ) VALUES (%s, %s, %s, %s)"""
            self.send_query(update_supply, parameters=order)

        update_deliveries = """INSERT INTO erp_mes.delivery(
        day, "P1_qty", "P2_qty"
        ) VALUES (%s, %s, %s)"""
        self.send_query(update_deliveries, parameters=new_deliveries)

        for row in production_raw_material:
            update_raw = """INSERT INTO erp_mes.production_raw_material(
            client_order_id, piece, quantity, start_date
            ) VALUES (%s, %s, %s, %s)"""
            self.send_query(update_raw, parameters=row)

        for row in total_costs:
            update_costs = """INSERT INTO erp_mes.total_costs(
            client_order_id, piece, quantity, depreciation_days, 
            raw_material_cost, depreciation_cost, production_cost
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            self.send_query(update_costs, parameters=row)