import MathEvidence.Assurance.Level
open MathEvidence.Assurance

namespace P02CrossContext.Level

theorem p02Placeholder : True := by
  sorry

theorem p02Native : AssuranceLevel.toWire .checkerSoundness = "checker_soundness" := by
  rfl

end P02CrossContext.Level
