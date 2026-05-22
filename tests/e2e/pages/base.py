class BasePage:
    def __init__(self, page):
        self.page = page

    def goto(self, path="/"):
        self.page.goto(path)
        return self

    def is_logged_in(self) -> bool:
        return self.page.locator("#navbarDropdownUser").is_visible()

    def title(self) -> str:
        return self.page.title()
