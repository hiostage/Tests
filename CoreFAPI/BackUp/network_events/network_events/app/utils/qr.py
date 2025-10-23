import qrcode
from io import BytesIO
from fastapi.responses import StreamingResponse

def generate_qr_code(data: str):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
