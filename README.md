# ENABLE2.0

This revised version of the original ENABLE program was designed to be more robust, versatile, and powerful than the original.

Current GUI:
![Screenshot](https://user-images.githubusercontent.com/9327832/27874743-9bd53248-617e-11e7-8e5a-04d02fa9e184.PNG)

ADMIN PASSWORDS:
Modify database path: Admin_10354

General login (located in usrp.yaml), hashed with md5
user: nih_general_user_1 --> hash: a5e079ad94245b3aaa97126eacf72cea
pass: ENABLE2PW1! --> hash: 79de4fb7d7846e9c24617587016572f9


Notes:

Changing patient objects to ordered list to utilize direct conversion of dict --> ordered list with built in functions
(makes mapping from the JSON obj back to something ENABLE can use much easier, perhaps faster)
https://stackoverflow.com/questions/1305532/convert-python-dict-to-object

Crash logging:
https://stackoverflow.com/questions/37780309/how-to-log-a-python-crash-in-windows
https://bitbucket.org/tebeka/crashlog/src
