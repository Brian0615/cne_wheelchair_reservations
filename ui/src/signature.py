import base64
import io

import numpy as np
from PIL import Image


class Signature:
    """Class to handle signature data."""

    def __init__(self, signature_data: np.ndarray):
        self.signature_data = signature_data
        self.size = signature_data.shape

    def to_bytes(self) -> io.BytesIO:
        """Encode self.signature_data signature as bytes."""
        signature = Image.fromarray(self.signature_data)
        signature_bytes = io.BytesIO()
        signature.save(signature_bytes, format="PNG")
        return signature_bytes

    def encode_as_base64(self) -> bytes:
        """Encode self.signature_data signature as base64."""
        return base64.b64encode(self.to_bytes().getvalue())

    @classmethod
    def decode_from_base64(cls, signature_bytes: bytes):
        """Decode a base64 encoded signature."""
        return cls(signature_data=np.array(Image.open(io.BytesIO(base64.b64decode(signature_bytes)))))

    @classmethod
    def load_from_file(cls, signature_path: str):
        """Load a signature from a file."""
        signature = Image.open(signature_path)
        return cls(signature_data=np.array(signature))
