# INFI ERP

Enterprise Resource Planning implementation for completion of FEUP's Industrial Informatics course.

To start ERP code, run `python3 main.py` and the program will start the main loop, connect to the UDP socket on port 24680 (make sure the firewall is accepting connection on this port), start the clock function and get the initial time on FEUP's database and start the threads needed for it to function correctly.

To test receiving new client orders in XML format, run `python3 send_udp.py`. After receiving the order, the code will manage it accordingly.

On each minute after after the initial time, the Master Planning Schedule will be created and the database updated.

For the code to run on production environment, both debug variables in `main.py` must be set to False.
