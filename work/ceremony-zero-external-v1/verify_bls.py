#!/usr/bin/env python3
"""Local BLS verification of drand rounds against the pinned chain public key.

Scheme: pedersen-bls-chained (drand default).
- digest(r) = SHA256(prev_signature || round_uint64_BIG_ENDIAN)
- public key on G1 (48-byte compressed), signatures on G2 (96-byte compressed)
- DST: BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_ (RFC 9380, == py_ecc G2Basic)
- randomness = SHA256(signature)

Sources pinned by inspection of drand master (crypto/schemes.go,
crypto/vault RandomnessFromSignature) on 2026-08-24.
"""
import hashlib
import json
import os
import sys

from py_ecc.bls.ciphersuites import G2Basic as SUITE

CHAIN_PK_HEX = (
    "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c"
    "529eeda66c7293784a9402801af31"
)

BEACONS = {
    6404619: {
        "randomness": "3aa8eb3c37f98fb3efbffb5c6420d1fde2182d1e0e746f97e9dbb81cf5cf1d5f",
        "signature": "aefc6b3adab63486fc60138aba63f880c7cd7ae213d2ae5a5cf532d1c216f02d"
                     "421c0680d1f77a4d382ee873230e355419be7cc0f9c4fbce33cb5f084884"
                     "c755e67c62d98794b5172c383018304345ec73741d909557c271afd295f78"
                     "63a7595",
    },
    6404620: {
        "randomness": "b47252e7bee8e17faabac1031dd2dea1ca4ed5f432bde6d4d641ccf67ac9310a",
        "signature": "a9443a104b9b3ade041299a71a3f0b5f7b17109fb82828520b3603a3d6cca886c"
                     "0b6986dd7a80f66e5550c6e80f386b300aee7e7134cded52aca4dda5ed18e34ff"
                     "a602fd2ea2945d5da020c6e66b75b4e6adf8f2a88ceeaec533a3713ccfca86",
    },
    6404621: {
        "randomness": "581d3edadd899dc72e218043e35599ad82b03855ac27fb583abd874bf3ca4132",
        "signature": "8b6c6dc1d915206eec56699fb8844b864f10de496f912d7a1ee78fa334e7c118c"
                     "d0409741612bf206ea256f857a9931b02d5cfe62f5cf51c5354291fb6ecc425b3"
                     "f31787f38d0ee63775588d497b0e68f58f7f4c4b295a042f4db50930858b8e",
    },
    6404625: {
        "randomness": "dadf6e557e8a97de5284fbd94da689f9f833a8c95387deb1beea3ac1216f0bd9",
        "signature": "8bc0da908bdc16dbd11e08c937cd84e561f3c8f78f2337ddf6dd9ea3f6f9f8c3a"
                     "93460317add3136d570993f2e36d3ca1246a0a9937b8a3dfad9a393b89a00abf"
                     "b9fdf80a6ffae8bfed5f9cb3abd235b8ce7e1b25e3f3dc660bbafac27fb040c",
    },
    6404626: {
        "randomness": "a8e7a5d99cd16571eed79f884e81d4ff6a5eb96668e37073b755c068c62f5e6f",
        "signature": "af7fe8a32c1fbb5933d3e96576d5dbf861b68da87bc9d2d99fc5b556824e86950"
                     "44dd92ba883efb902bb3a0b2ed3896f02da7597a8fb296806e19956d72b231f70"
                     "d3ef6b4408d141c039683c04fecf3c89163904f803445c8b0fcb5af1d85cc2",
    },
    6404627: {
        "randomness": "6604e6badc6a0447365db70a90ecab65d2c654fbfde7eb584b571c590afc188e",
        "signature": "9618d751ff81ed3f82fd1e2fbb97d78a79ba8a11901eac0e3a12947e29bf5614b"
                     "28e89a0b5df002e3fb095329db433a216b2f2aabd73add8100b52455d9cccc588"
                     "92c9ebf881b441674d32efe5f64384c7a17e6477e7c91545df67ddf60fcf75",
    },
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def verify_round(round_no, prev_sig_bytes, sig_hex, rand_hex):
    sig = bytes.fromhex(sig_hex)
    msg = hashlib.sha256(prev_sig_bytes + round_no.to_bytes(8, "big")).digest()
    ok_bls = SUITE.Verify(bytes.fromhex(CHAIN_PK_HEX), msg, sig)
    ok_rand = sha(sig) == rand_hex
    return ok_bls, ok_rand


def main():
    pk_ok = SUITE.KeyValidate(bytes.fromhex(CHAIN_PK_HEX))
    print("KeyValidate(chain_pk)=%s" % pk_ok)
    if not pk_ok:
        sys.exit(1)

    results = {}
    all_ok = pk_ok

    # every CEREMONY round verified against its real predecessor's signature.
    # Rounds 6404619/6404625 appear only as predecessor sources for chaining;
    # they are not independently verified here (their own predecessors are
    # outside this evidence set).
    pairs = [(6404620, 6404619), (6404621, 6404620),
             (6404626, 6404625), (6404627, 6404626)]
    for rnd, prev in pairs:
        prev_bytes = (
            bytes.fromhex(BEACONS[prev]["signature"]) if prev else b"\x00" * 96
        )
        bls_ok, rand_ok = verify_round(
            rnd, prev_bytes, BEACONS[rnd]["signature"], BEACONS[rnd]["randomness"]
        )
        results[rnd] = {"bls": bls_ok, "rand": rand_ok}
        all_ok &= bls_ok and rand_ok
        print("round=%d bls=%s randomness_sha=%s" % (rnd, bls_ok, rand_ok))

    print("BLS_VERIFICATION: %s" % ("PASS" if all_ok else "FAIL"))

    out = {
        "chain_pk_sha256": sha(bytes.fromhex(CHAIN_PK_HEX)),
        "scheme": "pedersen-bls-chained",
        "dst": "BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_",
        "results": {str(k): v for k, v in results.items()},
        "verdict": "PASS" if all_ok else "FAIL",
    }
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "run", "bls_verification.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
