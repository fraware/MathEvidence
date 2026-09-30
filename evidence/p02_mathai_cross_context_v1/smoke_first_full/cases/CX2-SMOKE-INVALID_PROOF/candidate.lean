import MathEvidence.Assurance.Calculus
open MathEvidence.Checkers.Calculus
open MathEvidence.Assurance.Calculus

namespace P02CrossContext.Calculus

theorem p02Native (req : Request) (cert : Certificate) : referenceCheck req cert = checkBool req cert := by
  exact True.intro

end P02CrossContext.Calculus
