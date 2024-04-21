"""The transport adapter plugins"""

from conda.plugins import CondaTransportAdapter, hookimpl
from .adapter import OCIAdapter


@hookimpl
def conda_transport_adapters():
    yield CondaTransportAdapter(
        name="oci", scheme="oci", adapter=OCIAdapter
    )
