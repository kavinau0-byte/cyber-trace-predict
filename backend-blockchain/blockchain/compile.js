// Compiles AuditTrail.sol -> AuditTrail.json (ABI + bytecode)
// Run with: node compile.js
const fs = require("fs");
const path = require("path");
const solc = require("solc");

const contractPath = path.join(__dirname, "AuditTrail.sol");
const source = fs.readFileSync(contractPath, "utf8");

const input = {
  language: "Solidity",
  sources: { "AuditTrail.sol": { content: source } },
  settings: {
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
  },
};

const output = JSON.parse(solc.compile(JSON.stringify(input)));

if (output.errors) {
  const fatal = output.errors.filter((e) => e.severity === "error");
  output.errors.forEach((e) => console.error(e.formattedMessage));
  if (fatal.length) process.exit(1);
}

const contract = output.contracts["AuditTrail.sol"]["AuditTrail"];
const artifact = {
  abi: contract.abi,
  bytecode: "0x" + contract.evm.bytecode.object,
};

fs.writeFileSync(
  path.join(__dirname, "AuditTrail.json"),
  JSON.stringify(artifact, null, 2)
);
console.log("Compiled -> AuditTrail.json");
