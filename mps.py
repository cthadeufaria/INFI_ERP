from database import Database



class MPS:

    def __init__(self) -> None:
        pass


    def create_mps(self):
        self.db = Database()

        open_orders = self.get_orders()
        
        inventory_produced, inventory_raw = self.get_inventory()
        
        expedition_orders = self.expedition_orders(inventory_produced, open_orders)
        
        production_orders = self.production_orders(open_orders, expedition_orders, inventory_raw)

        next_open_orders = self.get_next_orders()

        demand = self.demand(next_open_orders, open_orders, expedition_orders, production_orders)

        self.create_production_plan(demand)

        self.create_purchasing_plan(demand)


    def get_orders(self):
        query = """SELECT * from "INFI".orders;"""  # TODO: get orders' status
        return self.db.send_query(query, fetch=True)


    def get_inventory(self):
        # TODO:create inventory tables
        query_prod = """SELECT * FROM "INFI".inventory_prod as ip
            WHERE ip.day = (SELECT MAX(ip.day) from "INFI".inventory_prod as ip);"""
        query_raw = """SELECT * FROM "INFI".inventory_raw as ir
            WHERE ir.day = (SELECT MAX(ir.day) from "INFI".inventory_raw as ir);""" 

        return self.db.send_query(query_prod, fetch=True), self.db.send_query(query_raw, fetch=True)
        

    def expedition_orders(self, inventory_produced, open_orders):
        return min(stock_finished, customer_orders)


    def production_orders(self, open_orders, expedition_orders, inventory_raw):
        return min(customer_orders - expedition_orders, stock_raw)

    
    def get_next_orders(self):
        # TODO get next orders with status pending from database
        pass


    def demand(self, next_open_orders, open_orders, expedition_orders, production_orders):
        return next_customer_orders + customer_orders - expedition_orders - production_orders


    def create_production_plan(self, demand):
        pass


    def create_purchasing_plan(self, demand):
        pass


    def update_inventory(self):
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