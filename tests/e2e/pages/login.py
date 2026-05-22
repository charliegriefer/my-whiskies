from .base import BasePage


class LoginPage(BasePage):
    def login(self, username: str, password: str) -> "LoginPage":
        self.page.goto("/login")
        self.page.fill("input[name=username]", username)
        self.page.fill("input[name=password]", password)
        self.page.click("input[type=submit][name=submit]")
        return self

    def error_message(self) -> str:
        return self.page.locator(".alert").inner_text()
