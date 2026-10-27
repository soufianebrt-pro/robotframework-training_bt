*** Settings ***
Library    ../CAN_Sim_Library_Wipers.py    ../wipers_can_db_adv.dbc

Suite Setup     Start Trace Recording    filename=wipers_bcm_testrun_output.asc

Suite Teardown  Run Keywords    Stop Trace Recording    AND    Close Bus
Test Setup      Clear Bus Queue

*** Test Cases ***
Verify Wiper Command Transmission
    [Documentation]    Test sending a MANUAL wiper command message
    [Tags]             Wipers    Functional    REQ_WIPERS_001
    
    Start Vehicle CAN Sim

    Node X Send Message   tester  BCM_VehicleStatus   IgnitionStatus=ON
    Sleep              200ms
    Node X Send Message   wipers_switch  BCM_WiperCommand    WiperCommandMode=Fast
    Sleep              200ms

    # Step 2: Node B ( BCM ) picks up updated input CAN signals and replies with status
    Node X Receive And Respond    bcm
    Sleep              500ms
    # Step 5: Verify that the BCM/Cluster Warning message is broadcasted correctly
    ${wipers_status}=     Get Node X Response    tester  Wipers_Status

    # Assertions based on DBC value tables (3 : WiperMotorCommand = "High")
    Should Be Equal As Integers    ${wipers_status}[WiperMotorCommand]   2    msg=Error: WiperMotorCommand does not match expected value "High".


Verify Auto Wiping Transmission
    [Documentation]    Test Auto wiping function
    [Tags]             Wipers    Functional
    
    Node X Send Message   tester  BCM_VehicleStatus   IgnitionStatus=ON
    Sleep              200ms
    Node X Send Message   wipers_switch  BCM_WiperCommand    WiperCommandMode=Auto
    
    Node X Send Message  rain_sensor    RainSensor_Data    RainSensorStatus=1
    Node X Send Message  rain_sensor    RainSensor_Data    RainIntensity=30

    Sleep              500ms

    # Step 2: Node B ( BCM ) picks up updated input CAN signals and replies with status
    Node X Receive And Respond    bcm
    # Step 3: Wait for vECU reaction time / processing window
    Sleep              500ms

    # Step 4: Verify that the BCM/Cluster Warning message is broadcasted correctly
    ${wipers_status}=     Get Node X Response    tester  Wipers_Status

    # Assertions based on DBC value tables
    Should Be Equal As Integers    ${wipers_status}[WiperFaultStatus]   0    msg=Error: WiperFaultStatus does not match expected value.
    Should Be Equal As Integers    ${wipers_status}[WiperCurrentState]   3    msg=Error: WiperCurrentState does not match expected value.
