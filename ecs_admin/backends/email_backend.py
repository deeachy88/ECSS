from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils.functional import cached_property

import ssl
class EmailBackend(SMTPBackend):
    @cached_property
    def ssl_context(self):
        if hasattr(self, 'ssl_certfile') and hasattr(self, 'ssl_keyfile'):
            if self.ssl_certfile or self.ssl_keyfile:
                ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
                ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
                return ssl_context
        # If ssl_certfile or ssl_keyfile is not present or empty
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context






