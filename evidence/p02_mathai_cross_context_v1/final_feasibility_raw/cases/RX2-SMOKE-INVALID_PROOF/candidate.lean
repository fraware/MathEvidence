import MathEvidence.Assurance.Counterexample
open MathEvidence.Assurance.Counterexample

namespace P02CrossContext.Counterexample

theorem p02Native : contract.claimsCompleteness = false := by
  exact True.intro

end P02CrossContext.Counterexample
