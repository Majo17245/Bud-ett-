export function Flash({ sp }: { sp: { ok?: string; blad?: string } }) {
  return (
    <>
      {sp.ok && <div className="flash ok" role="status">{sp.ok}</div>}
      {sp.blad && <div className="flash bad" role="alert">{sp.blad}</div>}
    </>
  );
}
