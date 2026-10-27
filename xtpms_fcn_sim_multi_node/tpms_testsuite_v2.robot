*** Settings ***
Library    tpms_multi_node_sim.py    tpms_can_db_v1.dbc

Suite Setup     Start TPMS Trace Recording    filename=tpms_run_output_v2.asc

Suite Teardown  Run Keywords    Stop TPMS Trace Recording    AND    Close Bus
Test Setup      Clear Bus Queue


*** Test Cases ***
Verify TPMS Low Pressure Triggers Cluster Warning
    [Documentation]    Injects a low pressure signal for the Front-Left tire 
    ...                and validates that the BCM outputs the correct cluster warning.
    [Tags]             TPMS    Functional
    
    # Step 1: Send normal baseline signals for all tires
    Node X Send Message   tpms_sensors  TPMS_Data_FL  TPMS_Status_FL=2    TPMS_Pressure_FL=120

    # Step 2: Node B ( BCM ) picks up command and replies with status
    Node X Receive And Respond    bcm  TPMS_Data_FL
    
    # Step 4: Wait for vECU reaction time / processing window
    Sleep              500ms

    # Step 5: Verify that the BCM/Cluster Warning message is broadcasted correctly
    ${warning_msg}=     Receive Node X Response    cluster_display  BCM_TPMS_Warning_Cluster

    # Assertions based on DBC value tables
    Should Be Equal As Integers    ${warning_msg}[BCM_Global_Warning_ID]   3    msg=Error: Front_Left_Low warning ID not set by BCM!
    Should Be Equal As Integers    ${warning_msg}[BCM_Telltale_Lamp_Cmd]   2    msg=Error: Telltale lamp command should be Flashing (2)!