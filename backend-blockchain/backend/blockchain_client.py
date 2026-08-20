"""
Thin wrapper around web3.py for the AuditTrail smart contract.

Dev/demo mode: uses eth-tester, an in-memory Ethereum chain that needs no
external node — perfect for hackathon demos and for running inside CI.
To point at a real local testnet instead (Ganache/Hardhat), swap
EthereumTesterProvider() for Web3.HTTPProvider("http://127.0.0.1:8545")
and set DEPLOYER_ADDRESS / PRIVATE_KEY from your node's accounts.
"""
import json
import hashlib
from pathlib import Path
from web3 import Web3, EthereumTesterProvider

ARTIFACT_PATH = Path(__file__).parent.parent / "blockchain" / "AuditTrail.json"


class AuditChain:
    def __init__(self):
        self.w3 = Web3(EthereumTesterProvider())
        self.w3.eth.default_account = self.w3.eth.accounts[0]

        artifact = json.loads(ARTIFACT_PATH.read_text())
        self.abi = artifact["abi"]
        bytecode = artifact["bytecode"]

        Contract = self.w3.eth.contract(abi=self.abi, bytecode=bytecode)
        tx_hash = Contract.constructor().transact()
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.address = receipt.contractAddress
        self.contract = self.w3.eth.contract(address=self.address, abi=self.abi)

    @staticmethod
    def hash_payload(payload: dict) -> bytes:
        """Deterministic keccak-free sha256->bytes32 hash of a JSON payload.
        We never store the payload itself on-chain, only its hash."""
        blob = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(blob).digest()

    def log_event(self, complaint_id: str, event_type: str, payload: dict) -> str:
        payload_hash = self.hash_payload(payload)
        tx_hash = self.contract.functions.logEvent(
            complaint_id, event_type, payload_hash
        ).transact()
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()

    def get_audit_trail(self, complaint_id: str) -> list[dict]:
        entries = self.contract.functions.getAuditTrail(complaint_id).call()
        return [
            {
                "complaint_id": e[0],
                "event_type": e[1],
                "payload_hash": e[2].hex(),
                "timestamp": e[3],
                "logged_by": e[4],
            }
            for e in entries
        ]


# Single shared instance for the FastAPI app's lifetime
audit_chain = AuditChain()
