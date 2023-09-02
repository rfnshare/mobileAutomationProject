import time
from time import sleep
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.usefixtures("setup")
class TestHomePage:
    def scroll_to_text(self, txt):
        scroll_expression = f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(' \
                            f'new UiSelector().text("{txt}"))'
        self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, scroll_expression)

    def test_fill_form(self):
        driver = self.driver
        driver.implicitly_wait(10)
        driver.find_element(by=By.ID, value='com.androidsample.generalstore:id/spinnerCountry').click()
        self.scroll_to_text("Bangladesh")
        driver.find_element(by=By.XPATH, value="//android.widget.TextView[@text='Bangladesh']").click()
        driver.find_element(by=By.ID, value="com.androidsample.generalstore:id/nameField").send_keys("Faroque")
        driver.hide_keyboard()
        driver.find_element(by=By.XPATH,
                            value="//android.widget.RadioButton[@resource-id='com.androidsample.generalstore:id/radioFemale']").click()
        driver.find_element(by=By.ID, value='com.androidsample.generalstore:id/btnLetsShop').click()
        time.sleep(5)

    def test_error_msg(self):
        driver = self.driver
        driver.implicitly_wait(10)
        driver.find_element(by=By.ID, value='com.androidsample.generalstore:id/spinnerCountry').click()
        self.scroll_to_text("Bangladesh")
        driver.find_element(by=By.XPATH, value="//android.widget.TextView[@text='Bangladesh']").click()
        driver.find_element(by=By.XPATH,
                            value="//android.widget.RadioButton[@resource-id='com.androidsample.generalstore:id/radioFemale']").click()
        driver.find_element(by=By.ID, value='com.androidsample.generalstore:id/btnLetsShop').click()
        err_msg = driver.find_element(by=By.XPATH, value="//android.widget.Toast[1]").text
        print(err_msg)
        assert "Please enter your name" in err_msg
        time.sleep(5)

    def test_shopping(self):
        self.test_fill_form()
        self.scroll_to_text("Jordan 6 Rings")
        # self.driver.find_element(by=By.XPATH, value="//android.widget.TextView[@text='Jordan 6 "
        #                                             "Rings']/parent::android.widget.LinearLayout//android.widget.TextView[@text='ADD TO CART']").click()
        products = self.driver.find_elements(by=By.ID, value="com.androidsample.generalstore:id/productName")
        for i in range(0, len(products)):
            print("->", products[i].text)
            if products[i].text == "Jordan 6 Rings":
                (self.driver.find_elements(by=By.ID, value="com.androidsample.generalstore:id/productAddCart"))[i].click()
        self.driver.find_element(by=By.ID, value='com.androidsample.generalstore:id/appbar_btn_cart').click()

        # validating product name
        cart = (By.XPATH, "//android.widget.TextView[@text='Cart']")
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.text_to_be_present_in_element(cart, "Cart"))
        print(self.driver.find_element(*cart).text)

        p_n = self.driver.find_element(by=By.ID, value="com.androidsample.generalstore:id/productName").text
        print(p_n)
        assert "Jordan 6 Rings" in p_n
        # validating product price
        p_p = self.driver.find_element(by=By.ID, value="com.androidsample.generalstore:id/totalAmountLbl").text
        print(p_p)
        assert "165.0" in p_p

