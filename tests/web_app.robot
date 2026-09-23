*** Settings ***
Library    Browser

*** Test Cases ***
Open Robot Website
    New Browser    chromium    headless=True
    New Page    https://robotframework.org
    ${title}=    Get Title
    Log    ${title}
    Close Browser
