(* Epistemic UI helpers for MathEvidence Studio (Product 09).

   Color alone is insufficient. Every state includes text and a detailed report.
   Never label Certified without Lean status.
*)

EpistemicLegend[] := Dataset[{
  <|"State" -> "Computed", "Meaning" -> "Backend/candidate only; not Lean-certified"|>,
  <|"State" -> "Tested", "Meaning" -> "Offline schema/digest checks; Lean not asserted"|>,
  <|"State" -> "Certified", "Meaning" -> "Lean status present (witness/soundness/... verified)"|>,
  <|"State" -> "Ambiguous", "Meaning" -> "Rejected, unsupported, missing, or verified-without-Lean"|>
}];
