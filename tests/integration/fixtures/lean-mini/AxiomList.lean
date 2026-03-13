-- Axiom list producer: prints lines in contract format "declaration: axiom1, axiom2"
-- for the gateway's AxiomAuditorReal (AxiomAuditResult.dependencies).
-- Uses Lean.collectAxioms to report per-declaration axiom dependencies from the Environment
-- at compile time; run via `lake exe axiom_list` after `lake build`.
import Lean
import Lean.Meta
import Lean.Util.CollectAxioms
import Mini

open Lean Meta

/-- Build a string report of declaration names and their axiom dependencies (one line per declaration). -/
def formatAxiomReport : MetaM String := do
  let env ← getEnv
  let mut lines : Array String := #[]
  let names := env.constants.fold (fun (acc : List Name) (n : Name) (_ : ConstantInfo) => n :: acc) []
  for name in names do
    let axs ← Lean.collectAxioms name
    let axStrs := axs.toList.map toString
    let line := toString name ++ ": " ++ ", ".intercalate axStrs
    lines := lines.push line
  return String.intercalate "\n" (lines.toList)

def report : String := by
  let e ← run_meta (do
    let s ← formatAxiomReport
    toExpr s)
  exact e

def main : IO Unit :=
  IO.println report
