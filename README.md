# ITaccountant
#### Video Demo: <https://youtu.be/YtlqajTN7lg>
#### Description:
    The project is designed for people tha work as individual entrepreneurs in IT sector in Ukraine.
It can help to manage financial reports to fiscal service.
#### Log In:
    Has 2 fields: username and password. After user has clicked submit button there are two validations: if the username is present
    and if the password is present. Next step is to check whether the entered password corresponds with the entered username in DB.
    If all the validations are passed the user_id is remembered in session and user is redirected to the home page
#### Index:
    On the homepage the user enters sum of income, chooses currency, date and click on "submit" button. There are validations on the front side to check
    if the income sum is numeric, currency is ENUM (UAH, USD, EUR), date has format y-m-d. After that on back end there is a validation if all data
    are present.
    Next the application get the currency exchange rate from NBU API for entered date and currency in order to convert the entered sum to the ukrainian currency.
    If the entered currency is UAH the rate will be set to 1.
    After all the calculations the data are inserted to the db table transactions.
    And the user is redirected to transactions page.
#### Transactions:
    After that the user is redirected to the transactions page where he can see all the transactions being
made sorted by the date. The present columns in the transaction table are sum, currency, rate, uah, date.
    The user also has option to delete the transaction if a mistake was made.
#### Report:
    On a report page the user can generate a report for the range of dates. This report includes such values
as gross income, tax needs to be paid, Unified Social Contribution to be paid and net income. Gross incmome calculates
just by adding all the income values in uah for the range of date, tax is 5% from the gross income, to calculate usc
we need to count the quantity of the months in the date ranges and than to get a corresponding usc for every month
and after that to sum all this values, to get a net income from gross income subtract tax and usc.
#### Reference:
    Also there is a reference page where the user can see the tax calendar for current year.
#### Change password
    The user is able to change his password by accessing the form via the main menu.
    There are three fields: old password, new password and confirm password. After the user clicks submit
    first in back end there will be a check wether user has provided all data, next the system will check if old
    password is correct and after that check whether the new password equals confirmation password. After all this checks
    the password will be updated in the database
#### Log out:
    The user has an ability to log out from his account. The logic beyond that is simple:
    after clicking on log out button the user will be redirected to the login page where at first step
    the system will clear users session.