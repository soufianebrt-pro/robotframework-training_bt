import time
import can
import cantools

from robot.api.deco import keyword
import wipers_fcn_bcm_logic as bcm_logic

class CAN_Sim_Library_Wipers:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    """ vECU for Wipers Function Feature with in Body Control Module (BCM)"""
    def __init__(self, dbc_file_path):
            self.db = cantools.database.load_file(dbc_file_path)
            # Node A: Transmit into the Bus (Wiper Switch)

            self.bus_wipers_switch= can.interface.Bus(
                bustype='virtual', 
                channel='wipers_can_bus', 
                bitrate=500000
            )
            
            # (Simulates Node B (BCM) listening on the network)
            self.bus_bcm = can.interface.Bus(
                bustype='virtual', 
                channel='wipers_can_bus', 
                bitrate=500000
            )

            # (Simulates Node C (Wiper Motor) listening on the network)
            self.bus_wiper_motor = can.interface.Bus(
                bustype='virtual', 
                channel='wipers_can_bus', 
                bitrate=500000
            )

            # (Simulates Node D (Rain_Sensor) listening on the network)
            self.bus_rain_sensor = can.interface.Bus(
                bustype='virtual', 
                channel='wipers_can_bus', 
                bitrate=500000
            )

            # (Simulates Node E (Tester) listening on the network)
            self.bus_tester = can.interface.Bus(
                bustype='virtual', 
                channel='wipers_can_bus',
                bitrate=500000
            )

            self.Logger = None
            self.notifier_bcm = None
            self.notifier_wiper_motor = None
            self.notifier_tester = None

            self.node_bcm_reader = can.BufferedReader()
            self.node_wiper_motor_reader = can.BufferedReader()
            self.node_tester_reader = can.BufferedReader()

            # Dictionary to store the persistent state of each message frame
            self.message_state_cache = {}

            self.available_receiving_nodes = {"bcm": self.node_bcm_reader,
                                               "wiper_motor": self.node_wiper_motor_reader,
                                               "tester" : self.node_tester_reader}

            self.available_sending_nodes = {"wipers_switch": self.bus_wipers_switch,
                                             "bcm": self.bus_bcm,
                                             "wiper_motor": self.bus_wiper_motor,
                                             "rain_sensor": self.bus_rain_sensor,
                                             "tester" : self.bus_tester}


            self.available_out_messages = {"wipers_switch": ["BCM_WiperCommand"],
            "bcm":["Wipers_Status"],
            "wiper_motor":["WiperMotor_Data"],
            "rain_sensor":["RainSensor_Data"],
            "tester" : ["BCM_VehicleStatus"]
            }
            self.available_in_messages = {
                "bcm": ["BCM_VehicleStatus","RainSensor_Data", "BCM_WiperCommand"],
            }

            self.periodic_tasks = {}  # To keep track of periodic tasks for cleanup


    ############################################
    ############################################

    @keyword
    def start_vehicle_can_sim(self):
        """ Start the Vehicle Simulation """

        ### Fill the CAN Network with the initial values of all the signals in the DBC file
        for component, messages in self.available_out_messages.items():
            for message in messages:
                print(f"{component} -> {message}")
                signals = self.db.get_message_by_name(message).signals
                self.message_state_cache[message] = {sig.name: 0 for sig in signals}
        
        print(f"Starting periodic sending for node: {self.available_sending_nodes.keys()}")

        ## Send the initial values of all the signals in the DBC file to the CAN Bus
        for s_node_name, s_bus in self.available_sending_nodes.items():
            for s_msg in self.available_out_messages.get(s_node_name.lower(), []):
                message_def = self.db.get_message_by_name(s_msg)
                current_data = self.message_state_cache[s_msg]

                # 3. Encode the complete CAN data into raw payload bytes
                data = self.db.encode_message(s_msg, current_data)
                
                msg = can.Message(
                    arbitration_id=message_def.frame_id, 
                    data=data, 
                    is_extended_id=False
                )
                task = s_bus.send_periodic(msg,0.2)

                self.periodic_tasks[s_msg] = task  # Store the task for later cleanup

    @keyword
    def reset_can_network(self):
        """ Reset the CAN Network to its initial state """
        print("CAN network has been reset to its initial state.")
    
    @keyword
    def node_x_send_message(self, node, message_name, **signal_values):
        """
        Node A encodes and broadcasts 
        a command signal onto the bus.
        """
        message_def = self.db.get_message_by_name(message_name)

        # 1. If this message has never been sent, initialize all signals to 0
        if message_name not in self.message_state_cache:
            self.message_state_cache[message_name] = {sig.name: 0 for sig in message_def.signals}
        
        # 2. Get the current cached state for this message
        current_data_dict = self.message_state_cache[message_name]
        
        # 3. Update only the signals provided
        for sig_name, val in signal_values.items():
            if sig_name in current_data_dict:
                try:
                    # Smart type-casting for floats, ints, or strings
                    if '.' in str(val):
                        current_data_dict[sig_name] = float(val)
                    elif str(val).lstrip('-').isdigit():
                        current_data_dict[sig_name] = int(val)
                    else:
                        current_data_dict[sig_name] = val
                except ValueError:
                    current_data_dict[sig_name] = val
            else:
                raise KeyError(f"Signal '{sig_name}' does not exist in message '{message_name}'!")

        # 3. Encode the complete dictionary into raw payload bytes
        data = self.db.encode_message(message_name, current_data_dict)
        cmd_msg = can.Message(
            arbitration_id=message_def.frame_id, 
            data=data, 
            is_extended_id=False)
        # Modify the existing periodic task to send the new data
        self.periodic_tasks[message_name].modify_data(cmd_msg)
        while True:
            msg = self.node_bcm_reader.get_message(timeout=0.1)
            if msg is None:
                break
        print(f"[Node {node}] Sent {hex(message_def.frame_id)}: {current_data_dict}")


    """ Node B receives the command from Node A and responds with a system Status """
    @keyword
    def node_x_receive_and_respond(self, node):
        """
        Simulates this behavior: 
        1. Listens for Node command.
        2. Validates it & Sends back a response status message
        """
        ## 1. Loop through all the input CAN Messages of BCM
        for in_msg in self.available_in_messages.get(node.lower(), []):
            input_cmd_def = self.db.get_message_by_name(in_msg)
            receiving_node = self.available_receiving_nodes.get(node.lower())

            target_id = input_cmd_def.frame_id
            timeout= 2.0
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                remaining_time = float(timeout) - (time.time() - start_time)
                received_msg = receiving_node.get_message(timeout=max(0.1, remaining_time))
                if not received_msg:
                    continue
                if received_msg.arbitration_id != target_id:
                    print(f"[Node {node}] Getting message {received_msg.arbitration_id}... Not the correct one, waiting for {target_id}...")
                    continue
                if received_msg.arbitration_id == target_id:
                    decoded_in_cmd = self.db.decode_message(
                                received_msg.arbitration_id, 
                                received_msg.data, 
                                decode_choices=True
                            )
                    print(f"Command Recieved {in_msg}: {decoded_in_cmd}")
                    '''
                    for each input frame processed, the the values are stocked 
                    in the message_state_cache dictionary for future reference
                    ''' 
                    self.message_state_cache[in_msg] = decoded_in_cmd

                    ###################################
                    # SW Model implemenation for Wipers Function
                    # (Virtual ECU)
                    ###################################

                    ### if Wiper command OFF or manual ==> Activate REQ 1
                    ### if wiper command Auto ==> Activate REQ 2


                    
                    print(f"Decoded input BCM Message {in_msg} stored in message_state_cache: {self.message_state_cache[in_msg]}")
                    print(f"-----------------------------------------------")

                    response_allowed = False
                    resp_def = None
                    resp_data_dict = None
                    resp_data = None
                    
                    if node.lower() == "bcm" and in_msg == "BCM_VehicleStatus":
                        print("logic vehicle speed")
                    elif node.lower() == "bcm" and in_msg == "RainSensor_Data":
                        print("logic auto wiping")
                    elif node.lower() == "bcm" and in_msg == "BCM_WiperCommand" and decoded_in_cmd["WiperCommandMode"] in ["Off", "Slow", "Fast"]:
                        resp_def, resp_data_dict, resp_data = bcm_logic.get_bcm_manual_wipers_status(self.db,self.message_state_cache)
                        response_allowed = True
                    elif node.lower() == "bcm" and in_msg == "BCM_WiperCommand" and decoded_in_cmd["WiperCommandMode"] == "Auto":
                        resp_def, resp_data_dict, resp_data = bcm_logic.get_bcm_auto_wiping_status(self.db,self.message_state_cache)
                        response_allowed = True

                    if response_allowed:
                        resp_msg = can.Message(
                            arbitration_id=resp_def.frame_id, 
                            data=resp_data, 
                            is_extended_id=False)

                        # Modify the existing periodic task to send the new data

                        self.periodic_tasks[resp_def.name].modify_data(resp_msg)
                        while True:
                            msg = self.node_tester_reader.get_message(timeout=0)
                            if msg is None:
                                    break
                        print(f"[Node {node}] Responses is sent for the CAN Message {resp_def.name} ID {hex(resp_def.frame_id)}: {resp_data_dict}")

                        # the Current Node transmits its status back onto the bus
                        """
                        sending_node = self.available_sending_nodes.get(node.lower())
                        self.periodic_tasks[resp_def.name].stop()
                        self.periodic_tasks[resp_def.name] = sending_node.send_periodic(resp_msg, 0.2)
                        
                        """


                    
                    # Exit the loop after processing the command
                    break

                ###################################
                # END
                ###################################  
            else:
                raise AssertionError(f"[Node {node} ] Timeout: No command received")
        
 
    @keyword
    def get_node_x_response(self, node, response_message_name, timeout=2.0):
        """a Node listens for another Node's response frame to verify its behavior."""
        resp_def = self.db.get_message_by_name(response_message_name)
        target_id = resp_def.frame_id
        start_time = time.time()

        receiving_node = self.available_receiving_nodes.get(node.lower())
        print(f" Current available messages {self.message_state_cache.keys()}")

        while (time.time() - start_time) < timeout:
            remaining_time = float(timeout) - (time.time() - start_time)
            received_msg = receiving_node.get_message(timeout=max(0.1, remaining_time))

            if not received_msg:
                continue
            if received_msg.arbitration_id == target_id:
                decoded_signals = self.db.decode_message(
                            received_msg.arbitration_id, 
                            received_msg.data, 
                            decode_choices=False
                        )
                print(f" {response_message_name} Response Received: {decoded_signals} By the Node : {node}")
                return decoded_signals
        
        # If the loop finishes without finding the message, raise timeout error
        raise AssertionError(f"Timeout: Node {node} did not send message '{response_message_name}' (ID: {hex(target_id)}) within {timeout}s")
    
    @keyword
    def start_trace_recording(self, filename="can_bus_test_traces.asc"):
        """Starts recording CAN messages to a Vector-compatible file (.blf or .asc)
        using a virtual bus.
        """
        # Set up the logger (supports both .blf and .asc extensions)
        self.logger = can.Logger(filename)

        # Notifier for BCM bus (handles BCM reader and logger)
        self.notifier_bcm = can.Notifier(
            [self.bus_bcm], 
            [self.logger, self.node_bcm_reader]
        )

        # Notifier for Wiper Motor bus (handles Wiper_motor reader and logger)
        self.notifier_wiper_motor = can.Notifier(
            [self.bus_wiper_motor], 
            [self.logger, self.node_wiper_motor_reader],
        )

        self.notifier_tester = can.Notifier(
            [self.bus_tester], 
            [self.logger, self.node_tester_reader],
        )

        print(f"Started recording CAN trace to {filename}")

    @keyword
    def stop_trace_recording(self):
        """Stops the recording, flushes the file, and shuts down the bus."""

        if self.notifier_bcm:
            self.notifier_bcm.remove_listener(self.logger)
            self.notifier_bcm.stop(timeout=2)
            print(f"Notifier: {self.notifier_bcm.listeners}")
        if self.notifier_wiper_motor:
            self.notifier_wiper_motor.remove_listener(self.logger)
            self.notifier_wiper_motor.stop(timeout=2)
            print(f"Notifier: {self.notifier_wiper_motor.listeners}")
        if self.notifier_tester:
            self.notifier_tester.remove_listener(self.logger)
            self.notifier_tester.stop(timeout=2)
            print(f"Notifier: {self.notifier_tester.listeners}")
        
        time.sleep(1)

        if self.logger:
            self.logger.stop()
        print("Stopped CAN trace recording.")

    @keyword
    def close_bus(self):
        for task in self.periodic_tasks.values():
            task.stop()
        self.periodic_tasks.clear()
        
        if self.bus_wipers_switch:
            self.bus_wipers_switch.shutdown()
        if self.bus_bcm:
            self.bus_bcm.shutdown()
        if self.bus_wiper_motor:
            self.bus_wiper_motor.shutdown()
        if self.bus_rain_sensor:
            self.bus_rain_sensor.shutdown()
        if self.bus_tester:
            self.bus_tester.shutdown()
    
    @keyword
    def clear_bus_queue(self):
        """Clears any lingering messages from the virtual bus buffer."""
        while self.bus_bcm.recv(timeout=0.01):
            pass

    
    def __del__(self):
            try:
                self.close_bus()
            except:
                pass



