import can
import cantools
from robot.api.deco import keyword

class two_node_sim:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, dbc_file_path):
            self.db = cantools.database.load_file(dbc_file_path)
            
            # Node A: Transmit Bus (Simulates the Tester / Controller)
            self.wiper_switch_bus = can.interface.Bus(
                bustype='virtual', 
                channel='car_can_bus', 
                bitrate=500000
            )
            
            # Node B: Receive/Response Bus (Simulates Node B listening on the network)
            self.bcm_bus = can.interface.Bus(
                bustype='virtual', 
                channel='car_can_bus', 
                bitrate=500000
            )


    @keyword
    def clear_bus_queue(self):
        """Clears any lingering messages from the virtual bus buffer."""
        while self.bcm_bus.recv(timeout=0.01):
            pass

    @keyword
    def close_bus(self):
        if self.wiper_switch_bus:
            self.wiper_switch_bus.shutdown()
        if self.bcm_bus:
            self.bcm_bus.shutdown()

    @keyword
    def node_a_send_command(self, message_name, signal_name, value, periodic=False, interval=0.2):
        """
        Node A (Tester) encodes and broadcasts 
        a command signal onto the bus.
        """
        message_def = self.db.get_message_by_name(message_name)
        
        try:
            if isinstance(value, str) and not value.isdigit():
                parsed_value = value 
            elif '.' in str(value):
                parsed_value = float(value)
            else:
                parsed_value = int(value)
        except ValueError:
            parsed_value = value
        # Fill all signals in the message frame
        data_dict = {sig.name: 0 for sig in message_def.signals}
        data_dict[signal_name] = parsed_value
        data = message_def.encode(data_dict)
        
        msg = can.Message(
            arbitration_id=message_def.frame_id, 
            data=data, 
            is_extended_id=message_def.is_extended_frame
        )
        self.wiper_switch_bus.send(msg)
        print(f"[Node A] Sent {message_name}: {data_dict}")

    @keyword
    def node_b_receive_and_respond(self, command_message_name):
        """
        Simulates Node B behavior: 
        1. Listens for Node A's command.
        2. Validates it.
        3. Sends back a response status message (SW Module for Managing Wipers activation).
        """
        cmd_def = self.db.get_message_by_name(command_message_name)
        
        # Step 1: Node B listens for incoming command from Node A
        received_msg = self.bcm_bus.recv(timeout=2.0)
        if not received_msg:
            raise AssertionError(f"[Node B] Timeout: No command received from Node A")
            
        if received_msg.arbitration_id != cmd_def.frame_id:
            raise AssertionError(f"Expected Command ID {hex(cmd_def.frame_id)}, got {hex(received_msg.arbitration_id)}")
            
        decoded_cmd = self.db.decode_message(
            received_msg.arbitration_id,
            received_msg.data, decode_choices=False
        )
        print(f"[Node B] Received command from Node A: {decoded_cmd}")

        """
          Step 2: Node B processes command and replies with a Status message 
          (e.g., Wipers_Status)
        """

        resp_def = self.db.get_message_by_name("Wipers_Status")
        resp_data_dict = {sig.name: 0 for sig in resp_def.signals}

        ###################################
        ###################################
        # SW Model implemenation for Wipers (Req 1,2) (Virtual ECU)
        ###################################
        ###################################

        sig_wiper_command = decoded_cmd.get("WiperCommandMode")
        # sig_ignition_on = decoded_engine_cmd.get("IgnitionStatus")
        


        print(f" Value of wiper command sent by Node A : {sig_wiper_command} ")
        #Define Wipers Output Msg
        if sig_wiper_command == int(2):
            resp_data_dict["WiperCurrentState"] = int(4)
            resp_data = resp_def.encode(resp_data_dict)
            resp_msg = can.Message(
                arbitration_id=resp_def.frame_id, 
                data=resp_data, 
                is_extended_id=resp_def.is_extended_frame
            )
        else:
            resp_data_dict["WiperCurrentState"] = int(0)
            resp_data = resp_def.encode(resp_data_dict)
            resp_msg = can.Message(
                arbitration_id=resp_def.frame_id, 
                data=resp_data, 
                is_extended_id=resp_def.is_extended_frame
            )
        
        # Node B transmits its status back onto the bus
        self.wiper_switch_bus.send(resp_msg)
        print(f"[Node B] Responses is sent for the CAN Message <Wipers_Status>")

    @keyword
    def tester_receive_node_b_response(self, response_message_name, timeout=2.0):
        """Tester listens for Node B's response frame to verify Node B's behavior."""
        resp_def = self.db.get_message_by_name(response_message_name)
        
        received_msg = self.bcm_bus.recv(timeout=float(timeout))
        if not received_msg:
            raise AssertionError(f"Timeout: Node B did not send a response message for '{response_message_name}'")
            
        if received_msg.arbitration_id != resp_def.frame_id:
            raise AssertionError(f"Expected Response ID {hex(resp_def.frame_id)}, got {hex(received_msg.arbitration_id)}")
            
        decoded_signals = self.db.decode_message(
            received_msg.arbitration_id, 
            received_msg.data, 
            decode_choices=False
        )
        return decoded_signals

    def __del__(self):
            try:
                self.close_bus()
            except:
                pass
