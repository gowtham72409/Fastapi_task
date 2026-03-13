def fill(page,name,email):

    page.fill("#name",name)
    page.fill("#email",email)
    page.click("button[type=submit]")

    return "Form submitted"