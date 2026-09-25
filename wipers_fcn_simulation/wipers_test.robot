*** Settings ***
Library    CanLibrary.py    wipers_can_db.dbc
Suite Teardown    Close Bus

*** Test Cases ***
Verify Wiper Mode Off
    [Documentation]    Test setting the wiper mode to 'Off' (value 0).
    Send Wiper Signal    BodyControlModule    WiperMode    0
    ${signals}=    Receive And Decode Wiper Message    BodyControlModule    timeout=1.0
    Should Be Equal As Numbers    ${signals}[WiperMode]    0

Verify Wiper Mode Slow
    [Documentation]    Test setting the wiper mode to 'Slow' (value 2).
    Send Wiper Signal    BodyControlModule    WiperMode    2
    ${signals}=    Receive And Decode Wiper Message    BodyControlModule    timeout=1.0
    Should Be Equal As Numbers    ${signals}[WiperMode]    5

Verify Wiper Mode Fast
    [Documentation]    Test setting the wiper mode to 'Fast' (value 3).
    Send Wiper Signal    BodyControlModule    WiperMode    3
    ${signals}=    Receive And Decode Wiper Message    BodyControlModule    timeout=1.0
    Should Be Equal As Numbers    ${signals}[WiperMode]    3