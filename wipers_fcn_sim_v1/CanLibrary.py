import can
import cantools
from robot.api.deco import keyword

class CanLibrary:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, dbc_file_path):
        self.db = cantools.database.load_file(dbc_file_path)
        self.bus = can.interface.Bus(
            bustype='virtual', 
            channel='wiper_test_channel', 
            bitrate=500000, 
            receive_own_messages=True
        )

    
    @keyword
    def clear_bus_queue(self):
        """Clears any lingering messages from the virtual bus buffer."""
        while self.bus.recv(timeout=0.05):
            pass

    @keyword
    def send_wiper_signal(self, message_name, signal_name, value):
        """Encodes the wiper signal (accepts numbers or text like 'Fast') and sends it."""
        message_def = self.db.get_message_by_name(message_name)
        
        # Intelligently parse value: keep text as string, convert numeric strings to int/float
        try:
            if isinstance(value, str) and not value.isdigit():
                parsed_value = value  # e.g., 'Fast', 'Slow'
            elif '.' in str(value):
                parsed_value = float(value)
            else:
                parsed_value = int(value)
        except ValueError:
            parsed_value = value

        # Encode signal using cantools
        # BUILD DEFAULT DICTIONARY: Initialize all signals in this message to 0²
        data_dict = {sig.name: 0 for sig in message_def.signals}
        # Update the specific signal you passed in the keyword
        data_dict[signal_name] = parsed_value

        # Encode the full message dictionary
        data = message_def.encode(data_dict)
        
        # Send over virtual bus
        msg = can.Message(
            arbitration_id=message_def.frame_id, 
            data=data, 
            is_extended_id=message_def.is_extended_frame
        )
        self.bus.send(msg)
        print(f"Sent Message '{message_name}' ID: {hex(message_def.frame_id)} with {signal_name}={parsed_value}")

    @keyword
    def receive_and_decode_wiper_message(self, message_name, timeout=2.0):
        """Receives a message and decodes it back into raw numeric values."""
        message_def = self.db.get_message_by_name(message_name)
        
        received_msg = self.bus.recv(timeout=float(timeout))
        if not received_msg:
            raise AssertionError(f"Timeout: No CAN message received for '{message_name}'")
            
        if received_msg.arbitration_id != message_def.frame_id:
            raise AssertionError(f"Expected ID {hex(message_def.frame_id)}, got {hex(received_msg.arbitration_id)}")
            
        # decode_choices=False ensures we get the raw integer back (e.g., 3 instead of 'Fast')
        decoded_signals = self.db.decode_message(
            received_msg.arbitration_id, 
            received_msg.data, 
            decode_choices=False
        )
        return decoded_signals

    @keyword
    def close_bus(self):
        """Explicitly shuts down the virtual CAN bus to prevent warning logs."""
        if self.bus:
            self.bus.shutdown()

    def __del__(self):
        # Fallback safety close when Python garbage collects the object
        try:
            self.close_bus()
        except:
            pass