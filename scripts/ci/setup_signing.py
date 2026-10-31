"""Validate Actions signing secrets and prepare Gradle's private signing config."""
import argparse
import base64
import binascii
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


SECRET_NAMES = ("SIGNING_KEY", "KEY_STORE_PASSWORD", "ALIAS", "KEY_PASSWORD")


def property_value(value):
    """Escape values for java.util.Properties, including non-ASCII passwords."""
    escaped = []
    data = value.encode("utf-16-be", errors="surrogatepass")
    for index in range(0, len(data), 2):
        code = int.from_bytes(data[index:index + 2], "big")
        char = chr(code)
        if char in "\\:=#! ":
            escaped.append("\\" + char)
        elif code < 0x20 or code > 0x7e:
            escaped.append(f"\\u{code:04x}")
        else:
            escaped.append(char)
    return "".join(escaped)


def configure(project_root):
    missing = [name for name in SECRET_NAMES if not os.environ.get(name)]
    if missing:
        raise ValueError("Missing Actions secrets: " + ", ".join(missing))
    expected = os.environ.get("SIGNING_CERT_SHA256", "").lower().replace(":", "")
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Set repository variable SIGNING_CERT_SHA256 to the signing certificate SHA-256")
    try:
        key = base64.b64decode("".join(os.environ["SIGNING_KEY"].split()), validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("SIGNING_KEY must contain the Base64-encoded release keystore") from error
    if not key:
        raise ValueError("SIGNING_KEY decoded to an empty keystore")

    output = project_root / "app/keystore.properties"
    if output.exists():
        raise ValueError("app/keystore.properties already exists; refusing to replace it")
    keytool = Path(os.environ["JAVA_HOME"]) / "bin/keytool"
    work = Path(os.environ["RUNNER_TEMP"]) / "cyime-signing"
    work.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(work, 0o700)
    descriptor, filename = tempfile.mkstemp(prefix="release-", suffix=".jks", dir=work)
    keystore = Path(filename)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(key)
        common = [str(keytool), "-keystore", str(keystore), "-alias", os.environ["ALIAS"],
                  "-storepass:env", "KEY_STORE_PASSWORD"]
        certificate = subprocess.run(common + ["-exportcert"], capture_output=True, check=False)
        if certificate.returncode:
            raise ValueError("Keystore validation failed; check SIGNING_KEY, KEY_STORE_PASSWORD and ALIAS")
        fingerprint = hashlib.sha256(certificate.stdout).hexdigest()
        if fingerprint != expected:
            raise ValueError("Signing certificate does not match SIGNING_CERT_SHA256")
        # A certificate export does not unlock the private key; a CSR also checks KEY_PASSWORD.
        request = subprocess.run(common + ["-certreq", "-keypass:env", "KEY_PASSWORD"],
                                 capture_output=True, check=False)
        if request.returncode:
            raise ValueError("Private key validation failed; check KEY_PASSWORD")

        values = {"storeFile": str(keystore), "storePassword": os.environ["KEY_STORE_PASSWORD"],
                  "keyAlias": os.environ["ALIAS"], "keyPassword": os.environ["KEY_PASSWORD"]}
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="ascii") as stream:
            stream.write("".join(f"{name}={property_value(value)}\n" for name, value in values.items()))
        print("Validated release signing certificate SHA-256: " + fingerprint)
    except BaseException:
        keystore.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        configure(args.project_root.resolve())
    except (ValueError, KeyError, OSError) as error:
        print("::error::" + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
