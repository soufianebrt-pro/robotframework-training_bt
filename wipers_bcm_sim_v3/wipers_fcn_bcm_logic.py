import time

def get_bcm_manual_wipers_status(dbc,message_state_cache):
    resp_def = dbc.get_message_by_name("Wipers_Status")
    resp_data_dict = message_state_cache["Wipers_Status"]
    # REQ 1 & REQ 2

    ### input CAN Frame : "BCM_VehicleStatus" from External Tester to BCM 
    ### input CAN Frame : "BCM_WiperCommand" from Wiper Switch to BCM
    ### output CAN Frame : "Wiper_Status" from BCM to the Tester
    
    if message_state_cache["BCM_WiperCommand"]["WiperCommandMode"] == "Slow" and message_state_cache["BCM_VehicleStatus"]["IgnitionStatus"] == "ON":
        resp_data_dict["WiperCurrentState"] = 1
        resp_data_dict["WiperMotorCommand"] = 1

    elif message_state_cache["BCM_WiperCommand"]["WiperCommandMode"] == "Fast":
        resp_data_dict["WiperCurrentState"] = 2
        resp_data_dict["WiperMotorCommand"] = 2
    else :       
        resp_data_dict["WiperCurrentState"] = 0
        resp_data_dict["WiperMotorCommand"] = 0

    message_state_cache["Wipers_Status"] = resp_data_dict
    resp_data = resp_def.encode(resp_data_dict)

    return resp_def,resp_data_dict,resp_data

def get_bcm_auto_wiping_status(dbc,message_state_cache):
    resp_def = dbc.get_message_by_name("Wipers_Status")
    resp_data_dict = message_state_cache["Wipers_Status"]
    ## REQ 2 & REQ 5
 
    ### input CAN Frame : "RainSensor_Data" from Rain Sensor to BCM 
    ### input CAN Frame : "BCM_WiperCommand" from Wiper Switch to BCM
    ### output CAN Frame : "Wipers_Status" from BCM to the Tester

    if message_state_cache["RainSensor_Data"]["RainSensorStatus"] == 0:
        resp_data_dict["WiperCurrentState"] = 0
        resp_data_dict["WiperFaultStatus"] = "SENSOR_FAULT"
        resp_data_dict["WiperMotorCommand"] = 0
    
    elif message_state_cache["RainSensor_Data"]["RainSensorStatus"] == 1:
        ## Check Rain intensity Range to set Wiper Motor Speed
        resp_data_dict["WiperCurrentState"] = 3
        resp_data_dict["WiperFaultStatus"] = "Normal"
        resp_data_dict["WiperMotorCommand"] = 1
    else:
        resp_data_dict["WiperCurrentState"] = 0
        resp_data_dict["WiperFaultStatus"] = "Normal"
        resp_data_dict["WiperMotorCommand"] = 0
    
    # Update the message_state_cache with the new Wipers_Status
    message_state_cache["Wipers_Status"] = resp_data_dict
    resp_data = resp_def.encode(resp_data_dict)

    return resp_def,resp_data_dict,resp_data

def get_int_wiping_status(dbc,messag_state_cache,decoded_cmd_msg):
    # REQ 3 & REQ 4
    print("get_int_wiping_status function is called")

def update_wiper_motor_status(dbc,message_state_cache,decoded_cmd_msg):
    resp_def = dbc.get_message_by_name("WiperMotor_Data")

    resp_data_dict = {sig.name: 0 for sig in resp_def.signals}
 
    ### input CAN Frame : "Wiper_Status" from BCM to WiperMotor 
    ### output CAN Frame : "WiperMotor_Data" from WiperMotor to BCM

    if decoded_cmd_msg["WiperMotorCommand"] == "OFF":

        resp_data_dict["WiperMotorCurrent"] = "0"
        resp_data_dict["WiperParkSwitch"] = "ON"
    
    elif decoded_cmd_msg["WiperMotorCommand"] == "Low":
        ## Check Rain intensity Range to set Wiper Motor Speed
        resp_data_dict["WiperMotorCurrent"] = "1000"
        resp_data_dict["WiperParkSwitch"] = "OFF"

    elif decoded_cmd_msg["WiperMotorCommand"] == "High":

        resp_data_dict["WiperMotorCurrent"] = 2000
        resp_data_dict["WiperParkSwitch"] = "OFF"
    
    else:
        resp_data_dict = {sig.name: 0 for sig in resp_def.signals}        
        resp_data_dict["WiperMotorCurrent"] = 0
        resp_data_dict["WiperParkSwitch"] = 1
    
    resp_data = resp_def.encode(resp_data_dict)

    return resp_def,resp_data_dict,resp_data

