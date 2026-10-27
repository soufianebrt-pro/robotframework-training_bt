*** Settings ***
Library           two_node_sim.py    wipers_can_db_v3.dbc
Suite Teardown    Close Bus
Test Setup        Clear Bus Queue


*** Test Cases ***

Test Node B Responds To Wiper Command
    [Documentation]    Node A (Wiper_switch) sends a 'Slow' command; Node B (BCM) receives it and replies with 'Slow' status.
    
    # 1. Node A (Tester) sends command to turn wipers Slow
    Node A Send Command    BCM_WiperCommand    WiperCommandMode    Slow
    
    # 2. Node B (ECU under test) picks up command and replies with status
    Node B Receive And Respond    BCM_WiperCommand
    

    # 3. Test verifies Node B's response signal
    ${response_signals}=    Tester Receive Node B Response    Wipers_Status    timeout=1.0
    Should Be Equal As Numbers    ${response_signals}[WiperCurrentState]    3
