class FormTool:

    def fill_form(self, browser, selector, text):

        browser.type(selector, text)