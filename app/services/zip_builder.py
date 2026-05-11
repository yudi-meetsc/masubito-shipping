import io
import zipfile
from typing import Dict


def build(sub_zips: Dict[str, bytes]) -> bytes:
    """Bundle multiple named ZIP blobs into one master ZIP."""
    master_buf = io.BytesIO()
    with zipfile.ZipFile(master_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in sub_zips.items():
            if data:
                zf.writestr(name, data)
    return master_buf.getvalue()
