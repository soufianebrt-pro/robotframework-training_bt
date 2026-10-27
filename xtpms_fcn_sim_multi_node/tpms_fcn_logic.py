


## Simulating SW Component of Tpms inside BCM ECU
def getTPMSsystemStatus(decoded_cmd_msg):
    sig_tpms_fl_status= decoded_cmd_msg.get("TPMS_Status_FL")
    sig_tpms_global_warning_id = 0
    sig_tpms_telltale_lamp_cmd = 0

    if sig_tpms_fl_status in [0, 2]:
        sig_tpms_global_warning_id = 3
        sig_tpms_telltale_lamp_cmd = 2
        print(f" Tyre pressure is Normal for Front Left Tyre (Node A) ")
    else:
        sig_tpms_global_warning_id = 5
        sig_tpms_telltale_lamp_cmd = 3
        print(f" Tyre pressure is Low for Front Left Tyre (Node A) ")

    return [sig_tpms_global_warning_id, sig_tpms_telltale_lamp_cmd]