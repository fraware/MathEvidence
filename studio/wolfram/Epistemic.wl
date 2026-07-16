(* Epistemic UI helpers for MathEvidence Studio (Product 09).

   Color alone is insufficient. Every state includes text and a detailed report.
   Never label Certified without Lean status.
   Lean proposition + assumptions always precede the Certified affordance
   (see MathEvidenceStudio`CertificationSurface).
*)

EpistemicLegend[] := Dataset[{
  <|"State" -> "Computed", "Meaning" -> "Backend/candidate only; not Lean-certified"|>,
  <|"State" -> "Tested", "Meaning" -> "Offline schema/digest checks; Lean not asserted"|>,
  <|"State" -> "Certified", "Meaning" -> "Lean status + exact Lean proposition present"|>,
  <|"State" -> "Ambiguous", "Meaning" -> "Rejected, unsupported, missing, verified-without-Lean, or Lean-without-proposition"|>
}];
