using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace MagicExtract;

/// <summary>
/// The CK's auto-calculated spell cost, verified exactly against Enderal's own stored values
/// (_00E_A0_SteelTempestSP 07FB46, _00E_A1_ArcticWindSP 03C790 → 1565, the trap/cloak family):
///
///   effectCost    = floor( mgef.BaseCost * max(magnitude,1)^1.1 * durFactor^1.1 )
///   durFactor     = 1                                  when the MGEF is Concentration
///                   (duration==0 ? 10 : duration) / 10 otherwise
///   spellAutoCost = Σ effectCost      // per-effect floor THEN sum — rounding at the end is wrong
///
/// Concentration effects are charged PER SECOND, so their duration is ignored — found by
/// diffing computed vs stored across all 419 self-consistent base-Enderal spells: every
/// concentration mismatch (FlameBite 1.3·8^1.1 = 12.80 → 12, TrapFlames01 3·8^1.1 → 29, …)
/// resolves exactly under this rule.
///
/// Conditions on effects are ignored by the CK's calculation. Uses the WINNING MGEF's BaseCost,
/// so a mod that edits a shared MGEF shifts every auto-calc spell built on it (= costDrift).
/// </summary>
public static class CostCalculator
{
    public static int EffectCost(IMagicEffectGetter mgef, float magnitude, int duration)
    {
        double mag = Math.Max(magnitude, 1.0);
        double dur = mgef.CastType == CastType.Concentration
            ? 1.0
            : (duration == 0 ? 10.0 : duration) / 10.0;
        return (int)Math.Floor(mgef.BaseCost * Math.Pow(mag, 1.1) * Math.Pow(dur, 1.1));
    }

    /// <summary>Null when any effect's base MGEF is unresolvable (cost would be silently wrong).</summary>
    public static int? SpellAutoCost(IReadOnlyList<IEffectGetter>? effects,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef)
    {
        if (effects is null || effects.Count == 0) return 0;
        int sum = 0;
        foreach (var e in effects)
        {
            if (!winningMgef.TryGetValue(e.BaseEffect.FormKey, out var mgef)) return null;
            sum += EffectCost(mgef, e.Data?.Magnitude ?? 0, e.Data?.Duration ?? 0);
        }
        return sum;
    }
}
