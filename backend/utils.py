import base64


def convertpdf(pdf):
    with open(pdf, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())

    return encoded_string