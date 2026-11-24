"""Selenium dashboard test (page-object pattern).

Start the app first:  uvicorn app.main:app
Then run:             pytest selenium_tests -v
Set SPENDWISE_URL to test another address. Skipped when Selenium/Chrome is unavailable.
"""
import os
import urllib.request

import pytest

selenium = pytest.importorskip("selenium")
from selenium import webdriver  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

BASE_URL = os.environ.get("SPENDWISE_URL", "http://127.0.0.1:8000")


def _server_up():
    try:
        urllib.request.urlopen(BASE_URL + "/api/health", timeout=2)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _server_up(), reason=f"SpendWise not running at {BASE_URL}")


class DashboardPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    def open(self):
        self.driver.get(BASE_URL)
        return self

    def load_demo(self):
        self.driver.find_element(By.ID, "btn-demo").click()
        self.wait.until(lambda d: int(d.find_element(By.ID, "kpi-count").text or 0) > 0)

    def kpi(self, name):
        return self.driver.find_element(By.ID, f"kpi-{name}").text

    def alert_items(self):
        return self.driver.find_elements(By.CSS_SELECTOR, "#alerts-list li")

    def rows(self):
        return self.driver.find_elements(By.CSS_SELECTOR, "#txn-table tbody tr")


@pytest.fixture()
def driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    try:
        d = webdriver.Chrome(options=opts)  # Selenium Manager finds the driver
    except Exception as exc:
        pytest.skip(f"Chrome not available: {exc}")
    yield d
    d.quit()


def test_dashboard_loads_and_shows_report(driver):
    page = DashboardPage(driver).open()
    assert "SpendWise" in driver.title
    page.load_demo()
    assert int(page.kpi("count")) > 0
    assert len(page.rows()) > 0


def test_alerts_explain_why(driver):
    page = DashboardPage(driver).open()
    page.load_demo()
    items = [i for i in page.alert_items() if "Why flagged" in i.text]
    assert items, "expected at least one fraud alert with an explanation"
