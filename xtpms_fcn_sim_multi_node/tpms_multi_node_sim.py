import time
import can
import cantools

from robot.api.deco import keyword
from tpms_fcn_logic import getTPMSsystemStatus


class tpms_multi_node_sim:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    """ vECU for TPMS Feature with in Body Control Module (BCM)"""

    def __init__(self, dbc_file_path):
            self.db = cantools.database.load_file(dbc_file_path)
            # Node A: Transmit into the Bus (TPMS sensors)
            # (Simulates the inputs )

            self.tpms_sensors_bus = can.interface.Bus(
                bustype='virtual', 
                channel='tpms_can_bus', 
                bitrate=500000
            )
            
            # Receive/Response from the Bus 
            # (Simulates Node B (BCM) listening on the network)
            self.bus_bcm = can.interface.Bus(
                bustype='virtual', 
                channel='tpms_can_bus', 
                bitrate=500000
            )

            # (Simulates Node C (Cluster_HMI) listening on the network)
            self.bus_cluster_hmi = can.interface.Bus(
                bustype='virtual', 
                channel='tpms_can_bus', 
                bitrate=500000
            )

            self.Logger = None
            self.notifier_bcm = None
            self.notifier_cluster_hmi = None


            self.node_bcm_reader = can.BufferedReader()
            self.node_cluster_hmi_reader = can.BufferedReader()

            # Dictionary to store the persistent state of each message frame
            self.message_state_cache = {}

            self.available_receiving_nodes = {"bcm": self.node_bcm_reader,
                                               "cluster_display": self.node_cluster_hmi_reader}

            self.available_sending_nodes = {"tpms_sensors": self.tpms_sensors_bus,
                                             "bcm": self.bus_bcm,
                                             "cluster_display": self.bus_cluster_hmi}
    @keyword
    def clear_bus_queue(self):
        """Clears any lingering messages from the virtual bus buffer."""
        while self.bus_bcm.recv(timeout=0.01):
            pass

    
    @keyword
    def close_bus(self):
        if self.tpms_sensors_bus:
            self.tpms_sensors_bus.shutdown()
        if self.bus_bcm:
            self.bus_bcm.shutdown()
        if self.bus_cluster_hmi:
            self.bus_cluster_hmi.shutdown()

    """ Node Sending a command to the virtual Bus """
    @keyword
    def node_x_send_message(self, node, message_name, periodic=False, interval=0.2, **signal_values):
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
        
        msg = can.Message(
            arbitration_id=message_def.frame_id, 
            data=data, 
            is_extended_id=False
        )

        sending_node = self.available_sending_nodes.get(node.lower())
        sending_node.send_periodic(msg,0.2)

        print(f"[Node {node}] Sent {hex(message_def.frame_id)}: {current_data_dict}")



    """ Node B receives the command from Node A and responds with a system Status """
    @keyword
    def node_x_receive_and_respond(self, node, command_message_name):
        """
        Simulates this behavior: 
        1. Listens for Node command.
        2. Validates it.
        3. Sends back a response status message
        """
        cmd_def = self.db.get_message_by_name(command_message_name)
        
        receiving_node = self.available_receiving_nodes.get(node.lower())

        target_id = cmd_def.frame_id
        timeout= 2.0
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            remaining_time = float(timeout) - (time.time() - start_time)
            
            received_msg = receiving_node.get_message(timeout=max(0.1, remaining_time))
            print(received_msg)
            if not received_msg:
                continue
            if received_msg.arbitration_id != target_id:
                print(f"[Node {node}] Getting message {received_msg.arbitration_id}... Not the correct one, waiting for {target_id}...")
                continue
            if received_msg.arbitration_id == target_id:
                decoded_cmd = self.db.decode_message(
                            received_msg.arbitration_id, 
                            received_msg.data, 
                            decode_choices=False
                        )
                print(f" Command Recieved {command_message_name}: {decoded_cmd}")
        
                ###################################
                # SW Model implemenation for Tyre Pressure Warnings (Req 1,2)
                # (Virtual ECU)
                ###################################

                if command_message_name == "TPMS_Data_FL":
                    tpms_warning_status = getTPMSsystemStatus(decoded_cmd)
                    resp_def = self.db.get_message_by_name("BCM_TPMS_Warning_Cluster")
                    resp_data_dict = {sig.name: 0 for sig in resp_def.signals}
                    self.message_state_cache["BCM_TPMS_Warning_Cluster"] = resp_data_dict  # Initialize if not present
                    
                    resp_data_dict["BCM_Global_Warning_ID"] = tpms_warning_status[0]
                    resp_data_dict["BCM_Telltale_Lamp_Cmd"] = tpms_warning_status[1]
                    resp_data = resp_def.encode(resp_data_dict)

                    resp_msg = can.Message(
                        arbitration_id=resp_def.frame_id, 
                        data=resp_data, 
                        is_extended_id=False)
                    
                    # the Current Node transmits its status back onto the bus
                    sending_node = self.available_sending_nodes.get(node.lower())
                    sending_node.send_periodic(resp_msg, 0.2)
    
                    print(f"[Node {node}] Responses is sent for the CAN Message {resp_def.name} ID {hex(resp_def.frame_id)}: {resp_data_dict}")
                    break  # Exit the loop after processing the command
                else:
                    raise AssertionError(f"[Node {node}] Received unexpected command message: {command_message_name}")       
        else:
            raise AssertionError(f"[Node {node} ] Timeout: No command received")
        
 
    @keyword
    def receive_node_x_response(self, node, response_message_name, timeout=2.0):
        """Tester listens for Node X's response frame to verify its behavior."""
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
                print(f" {response_message_name} Response Received: {decoded_signals} from Node {node}")
                return decoded_signals
        # If the loop finishes without finding the message, raise timeout error
        raise AssertionError(f"Timeout: Node {node} did not send message '{response_message_name}' (ID: {hex(target_id)}) within {timeout}s")
    
    @keyword
    def start_tpms_trace_recording(self, filename="tpms_test_trace.blf"):
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

        # Notifier for ESP bus (handles ESP reader and logger)
        self.notifier_cluster_hmi = can.Notifier(
            [self.bus_cluster_hmi], 
            [self.logger, self.node_cluster_hmi_reader]
        )
        
        print(f"Started recording TPMS trace to {filename}")

    @keyword
    def stop_tpms_trace_recording(self):
        """Stops the recording, flushes the file, and shuts down the bus."""
        if self.notifier_bcm:
            self.notifier_bcm.stop()
        if self.notifier_cluster_hmi:
            self.notifier_cluster_hmi.stop()

        if self.logger:
            self.logger.stop()

        if self.bus_bcm:
            self.bus_bcm.shutdown()
        if self.bus_cluster_hmi:
            self.bus_cluster_hmi.shutdown()
        print("Stopped TPMS trace recording.")

        
    def __del__(self):
            try:
                self.close_bus()
            except:
                pass



