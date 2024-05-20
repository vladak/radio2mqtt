"""
hex dumping capability
adapted from https://gist.github.com/NeatMonster/c06c61ba4114a2b31418a364341c26c0
"""


class Hexdump:
    """
    simple hexdumping class - no squeezing, no address column
    """
    def __init__(self, buf):
        self.buf = buf

    def __iter__(self):
        for i in range(0, len(self.buf), 16):
            bs = bytearray(self.buf[i : i + 16])
            # pylint: disable=consider-using-f-string
            line = "{:23}  {:23}  |{:16}|".format(
                " ".join(("{:02x}".format(x) for x in bs[:8])),
                " ".join(("{:02x}".format(x) for x in bs[8:])),
                "".join((chr(x) if 32 <= x < 127 else "." for x in bs)),
            )
            yield line

        yield ""

    def __str__(self):
        return "\n".join(self)

    def __repr__(self):
        return "\n".join(self)
