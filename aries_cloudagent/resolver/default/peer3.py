"""Peer DID Resolver.

Resolution is performed by converting did:peer:2 to did:peer:3 according to 
https://identity.foundation/peer-did-method-spec/#generation-method:~:text=Method%203%3A%20DID%20Shortening%20with%20SHA%2D256%20Hash
DID Document is just a did:peer:2 document (resolved by peer-did-python) where 
the did:peer:2 has been replaced with the did:peer:3.
"""

import re
from hashlib import sha256
from typing import Optional, Pattern, Sequence, Text, Union, Tuple, List

from peerdid.dids import (
    DID,
    MalformedPeerDIDError,
    DIDDocument,
    DIDUrl,
)
from peerdid.keys import to_multibase, MultibaseFormat
from ...connections.base_manager import BaseConnectionManager
from ...config.injection_context import InjectionContext
from ...core.profile import Profile
from ...storage.base import BaseStorage
from ..base import BaseDIDResolver, DIDNotFound, ResolverType
from .peer2 import _resolve_peer_did_with_service_key_reference


class PeerDID3Resolver(BaseDIDResolver):
    """Peer DID Resolver."""

    def __init__(self):
        """Initialize Key Resolver."""
        super().__init__(ResolverType.NATIVE)

    async def setup(self, context: InjectionContext):
        """Perform required setup for Key DID resolution."""

    @property
    def supported_did_regex(self) -> Pattern:
        """Return supported_did_regex of Key DID Resolver."""
        return re.compile(r"^did:peer:3(.*)")

    async def _resolve(
        self,
        profile: Profile,
        did: str,
        service_accept: Optional[Sequence[Text]] = None,
    ) -> dict:
        """Resolve a Key DID."""
        if did.startswith("did:peer:3"):
            # retrieve did_doc from storage using did:peer:3
            async with profile.session() as session:
                storage = session.inject(BaseStorage)
                record = await storage.find_record(
                    BaseConnectionManager.RECORD_TYPE_DID_DOCUMENT, {"did": did}
                )
                did_doc = DIDDocument.from_json(record.value)
        else:
            raise DIDNotFound(f"did is not a did:peer:3 {did}")

        return did_doc.dict()


def gen_did_peer_3(peer_did_2: Union[str, DID]) -> Tuple[DID, DIDDocument]:
    """Generate did:peer:3 and corresponding DIDDocument."""
    if not peer_did_2.startswith("did:peer:2"):
        raise MalformedPeerDIDError("did:peer:2 expected")

    content = to_multibase(
        sha256(peer_did_2.lstrip("did:peer:2").encode()).digest(),
        MultibaseFormat.BASE58,
    )
    dp3 = DID("did:peer:3" + content)

    doc = _resolve_peer_did_with_service_key_reference(peer_did_2)
    _convert_to_did_peer_3_document(dp3, doc)
    return dp3, doc


def _replace_all_values(input, org, new):
    for k, v in input.items():
        if isinstance(v, type(dict)):
            _replace_all_values(v, org, new)
        if isinstance(v, List):
            for i, item in enumerate(v):
                if isinstance(item, type(dict)):
                    _replace_all_values(item, org, new)
                elif (
                    isinstance(item, str)
                    or isinstance(item, DID)
                    or isinstance(item, DIDUrl)
                ):
                    v.pop(i)
                    v.append(item.replace(org, new, 1))
                elif hasattr(item, "__dict__"):
                    _replace_all_values(item.__dict__, org, new)
                else:
                    pass

        elif isinstance(v, str) or isinstance(v, DID) or isinstance(v, DIDUrl):
            input[k] = v.replace(org, new, 1)
        else:
            pass


def _convert_to_did_peer_3_document(dp3, dp2_document: DIDDocument) -> None:
    dp2 = dp2_document.id
    _replace_all_values(dp2_document.__dict__, dp2, dp3)

    # update document indexes
    new_indexes = {}
    for ind, val in dp2_document._index.items():
        new_indexes[ind.replace(dp2, dp3)] = val

    dp2_document._index = new_indexes
