from utils import gen_keys, sign, verify, sha256, PublicKey

sk, pk = gen_keys()
msg = b"hello"
sig = sign(msg, sk)
assert verify(msg, sig, pk)
assert not verify(b"tampered", sig, pk)
print("OK: sign/verify + sha256 length =", len(sha256(b'x')))
