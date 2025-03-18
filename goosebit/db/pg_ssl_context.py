import logging
import ssl


class PostgresSSLContext:
    context: ssl.SSLContext

    def __init__(self):
        # create ssl context in server-auth mode: this sets verify_mode = required and check_hostname = True
        self.context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

    def parse_ssl_mode(self, sslmode: str):
        match sslmode:
            case "none":
                self.context.check_hostname = False
                self.context.verify_mode = ssl.CERT_NONE
            case "optional":
                self.context.verify_mode = ssl.CERT_OPTIONAL
            case "require":
                self.context.verify_mode = ssl.CERT_REQUIRED
            case _:
                logging.error("sslmode must be either: none, optional or required!")
                exit(1)

    # parse and set verify-flags according to postgres string attributes
    # default as defined in python3.13 lib/ssl.py: https://github.com/python/cpython/blob/3.13/Lib/ssl.py#L713)
    # is the following: (ssl.VERIFY_X509_PARTIAL_CHAIN | ssl.VERIFY_X509_STRICT)
    def parse_verify_flags(self, verifyflags: str):
        self.context.verify_flags = ssl.VerifyFlags(0)
        for f in verifyflags.split("|"):
            match f:
                case "default":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_DEFAULT
                case "crl_check_leaf":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_CRL_CHECK_LEAF
                case "crl_check_chain":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_CRL_CHECK_CHAIN
                case "x509_strict":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_X509_STRICT
                case "allow_proxy_certs":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_ALLOW_PROXY_CERTS
                case "x509_trusted_first":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_X509_TRUSTED_FIRST
                case "x509_partial_chain":
                    self.context.verify_flags |= ssl.VerifyFlags.VERIFY_X509_PARTIAL_CHAIN
                case _:
                    logging.error(f"verify-flag is undefined: {f}")
                    exit(1)

    def load_verify_locations(self, file):
        self.context.load_verify_locations(file)
