import qrcode
from io import BytesIO


def generate_ticket_qr(ticket):
    data = f"TICKET:{ticket.ticket_id}"
    qr = qrcode.make(data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
