def format_currency(amount):
    return f"${amount:,.2f}"


def validate_email(email):
    # A simple email validation function
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
