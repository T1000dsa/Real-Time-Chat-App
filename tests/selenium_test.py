from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from threading import Thread


def test_user(i):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    try:
        user_data = {
            'name': f'new_username_test{i}',
            'password': f'new_password_test{i}',
            'email': f'test_{i}@test.com'
        }

        driver.get("http://localhost:8000/v1/register")
        username_field_reg = driver.find_element(By.NAME, "login")
        password_field_reg = driver.find_element(By.NAME, "password")
        password_again_field_reg = driver.find_element(By.NAME, "password_again")
        email_field_reg = driver.find_element(By.NAME, "email") 
        submit_button_reg = driver.find_element(By.XPATH, "//button[@type='submit']")

        username_field_reg.send_keys(user_data["name"])
        password_field_reg.send_keys(user_data["password"])
        password_again_field_reg.send_keys(user_data["password"])
        email_field_reg.send_keys(user_data["email"])
        submit_button_reg.click()


    finally:
        driver.get("http://localhost:8000/v1/login")
        username_field = driver.find_element(By.NAME, "login")
        password_field = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")

        username_field.send_keys(user_data["name"])
        password_field.send_keys(user_data["password"])
        submit_button.click()

        #driver.get("http://localhost:8000/v1/logout")

        driver.quit()


# Create and start threads
threads = []
for i in range(15):
    t = Thread(target=test_user, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()