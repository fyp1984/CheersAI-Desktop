"""SSL configuration to force OpenSSL backend on Windows."""
import logging

logger = logging.getLogger(__name__)


def configure_ssl_backend():
    """
    Configure SSL backend to use OpenSSL instead of system default (schannel on Windows).
    
    This is necessary because some SSL servers (like uat-filebay.cheersai.cloud) have
    SSL configurations that work with OpenSSL/rustls but fail with Windows schannel.
    """
    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
        logger.info("Successfully injected pyOpenSSL into urllib3 - using OpenSSL backend")
        return True
    except ImportError:
        logger.warning(
            "pyOpenSSL not available. SSL connections to some servers may fail. "
            "Install with: pip install pyopenssl"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to inject pyOpenSSL: {e}")
        return False


# Auto-configure on module import
configure_ssl_backend()
