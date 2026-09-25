*** Settings ***
Library           CanLibrary.py    wipers_can_db_adv.dbc
Suite Teardown    Close Bus
Test Setup        Clear Bus Queue


*** Test Cases ***

Verify Wiper Command Transmission
    [Documentation]    Test sending a wiper command message.
    Send Wiper Signal    BCM_WiperCommand    WiperCommandMode    Fast
    Send Wiper Signal    BCM_WiperCommand    WiperWashRequest    1
    
    ${signals}=    Receive And Decode Wiper Message    BCM_WiperCommand    timeout=1.0
    Should Be Equal As Numbers    ${signals}[WiperCommandMode]    3
    Should Be Equal As Numbers    ${signals}[WiperWashRequest]    1

Verify Wiper Motor Status Feedback
    [Documentation]    Test decoding a status frame reported by the wiper motor.
    Send Wiper Signal    Wipers_Status    WiperCurrentState    Slow
    Send Wiper Signal    Wipers_Status    WiperParked          0
    
    ${signals}=    Receive And Decode Wiper Message    Wipers_Status    timeout=1.0
    Should Be Equal As Numbers    ${signals}[WiperCurrentState]    2
    Should Be Equal As Numbers    ${signals}[WiperParked]          0

Verify Rain Sensor Integration Data
    [Documentation]    Test scaling on rain intensity signal (factor 0.5).
    Send Wiper Signal    RainSensor_Data    RainIntensity      75
    
    ${signals}=    Receive And Decode Wiper Message    RainSensor_Data    timeout=1.0
    # 75 * 0.5 factor defined in DBC = 37.5 decoded value
    Should Be Equal As Numbers    ${signals}[RainIntensity]    37.5