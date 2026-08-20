// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title CyberTrace Predict — Audit Trail
/// @notice Immutable log of complaint lifecycle events (Stage 4 deliverable).
///         Deliberately dumb: it knows nothing about fraud, ML, or geography.
///         It just proves *what happened and when* for legal admissibility.
contract AuditTrail {

    struct AuditEntry {
        string complaintId;
        string eventType;     // "complaint_received" | "prediction_generated" | "alert_issued"
        bytes32 payloadHash;  // keccak256 hash of the actual payload (never store PII on-chain)
        uint256 timestamp;
        address loggedBy;
    }

    // complaintId => full ordered history of events for that complaint
    mapping(string => AuditEntry[]) public auditTrail;

    event EntryLogged(
        string indexed complaintId,
        string eventType,
        bytes32 payloadHash,
        uint256 timestamp,
        address loggedBy
    );

    /// @notice Append a new audit entry for a complaint. Entries can never be edited or removed.
    function logEvent(
        string memory complaintId,
        string memory eventType,
        bytes32 payloadHash
    ) public {
        AuditEntry memory entry = AuditEntry({
            complaintId: complaintId,
            eventType: eventType,
            payloadHash: payloadHash,
            timestamp: block.timestamp,
            loggedBy: msg.sender
        });

        auditTrail[complaintId].push(entry);

        emit EntryLogged(complaintId, eventType, payloadHash, block.timestamp, msg.sender);
    }

    /// @notice Return the full audit history for a complaint, in order.
    function getAuditTrail(string memory complaintId) public view returns (AuditEntry[] memory) {
        return auditTrail[complaintId];
    }

    /// @notice Convenience: how many events have been logged for a complaint.
    function getEntryCount(string memory complaintId) public view returns (uint256) {
        return auditTrail[complaintId].length;
    }
}
