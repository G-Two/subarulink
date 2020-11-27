# Copyright (C) 2018 Julien Hartmann
# This program is distributed under the MIT license, a copy of which you should
# have receveived along with it. If not, see <https://opensource.org/licenses/MIT>.
#
import contextlib
import datetime
import ssl
import tempfile

import pytest

# flake8: noqa


class TemporaryCertificate:
    """ Certificate representation used by :func:`ssl_certificate` fixture """

    def __enter__(self):
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        subject = issuer = x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, "localhost")])

        with contextlib.ExitStack() as stack:
            key = rsa.generate_private_key(public_exponent=65537, key_size=1024, backend=default_backend())

            key_file = stack.enter_context(tempfile.NamedTemporaryFile())
            key_file.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            key_file.flush()

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.utcnow())
                .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=1))
                .add_extension(
                    x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.DNSName("127.0.0.1"),]),
                    critical=False,
                )
                .sign(key, hashes.SHA256(), default_backend())
            )

            cert_file = stack.enter_context(tempfile.NamedTemporaryFile())
            cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
            cert_file.flush()

            self._key_file, self._cert_file = key_file, cert_file
            stack.pop_all()
        return self

    def __exit__(self, exc, exc_type, tb):
        self._key_file.close()
        self._cert_file.close()

    def load_verify(self, context):
        """Load the certificate for verification purposes.

        :param ssl.SSLContext context: a SSL context that will be associated with the server.
        """
        context.load_verify_locations(cafile=self._cert_file.name)

    def client_context(self):
        """ A client-side SSL context accepting the certificate, and no others """
        context = ssl.SSLContext()
        context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
        self.load_verify(context)
        return context

    def server_context(self):
        """ A server-side SSL context using the certificate """
        context = ssl.SSLContext()
        context.load_cert_chain(self._cert_file.name, keyfile=self._key_file.name)
        return context


@pytest.fixture(scope="session")
def ssl_certificate():
    """ Self-signed certificate fixture, used for local server tests. """
    with TemporaryCertificate() as certificate:
        yield certificate
