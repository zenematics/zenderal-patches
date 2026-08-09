using System.Buffers.Binary;
using System.Text;
using System.Text.Json.Nodes;
using MagicExtract.Projections;

namespace MagicExtract;

public sealed class SelfCheck(List<string> warnings)
{
    // ---- L2: cost formula validation -----------------------------------------------------

    /// <summary>
    /// Validates the auto-cost FORMULA in a clean context: base Enderal's own spells against
    /// base Enderal's own magic effects (Skyrim.esm only, no overrides in play). Here computed
    /// and stored must agree — any gap is formula error, not drift.
    ///
    /// Winner-context disagreement is deliberately NOT gated: an override that changes a shared
    /// MGEF's BaseCost (or a spell's durations) without recomputing the stored spell cost
    /// produces REAL drift — e.g. EGO's SteelTempest override changes durations 7/11/15 →
    /// 10/13/16 and keeps BaseCost 334, so the live auto-cost is 400. That drift is a
    /// rebalancing finding (costDrift), not a bug in this tool.
    /// </summary>
    public bool FormulaValidation(List<LoadedPlugin> loaded)
    {
        var basePlugin = loaded.FirstOrDefault(p => p.Entry.Name.Equals("Skyrim.esm", StringComparison.OrdinalIgnoreCase));
        if (basePlugin is null)
        {
            warnings.Add("Skyrim.esm not in load order?! cost formula unvalidated, cost model disabled");
            return false;
        }
        var baseMgef = new Dictionary<Mutagen.Bethesda.Plugins.FormKey, Mutagen.Bethesda.Skyrim.IMagicEffectGetter>();
        foreach (var m in basePlugin.Mod.MagicEffects) baseMgef[m.FormKey] = m;

        int total = 0, exact = 0;
        var buckets = new SortedDictionary<string, int>();
        foreach (var s in basePlugin.Mod.Spells)
        {
            if (s.Flags.HasFlag(Mutagen.Bethesda.Skyrim.SpellDataFlag.ManualCostCalc)) continue;
            // Only castable spells: Voice/Power/Ability costs are never charged, and base Enderal
            // ships authored junk in them (e.g. _00E_A2_GhostwalkSP stores 8981 on zero-cost effects).
            if (s.Type != Mutagen.Bethesda.Skyrim.SpellType.Spell) continue;
            var auto = CostCalculator.SpellAutoCost(s.Effects, baseMgef);
            if (auto is null) continue; // references an MGEF outside this plugin — not a clean sample
            total++;
            int drift = Math.Abs(auto.Value - (int)s.BaseCost);
            if (drift == 0) exact++;
            else if (Environment.GetEnvironmentVariable("MAGIC_EXTRACT_COST_DEBUG") == "1" && total < 500)
            {
                var fx = string.Join(" + ", s.Effects.Select(e =>
                    baseMgef.TryGetValue(e.BaseEffect.FormKey, out var m)
                        ? $"[bc={m.BaseCost} mag={e.Data?.Magnitude ?? 0} dur={e.Data?.Duration ?? 0}]"
                        : "[?]"));
                Console.WriteLine($"MISMATCH {s.EditorID} cast={s.CastType} type={s.Type} " +
                                  $"stored={s.BaseCost} computed={auto} :: {fx}");
            }
            string bucket = drift switch
            {
                0 => "exact", <= 2 => "±1–2", <= 10 => "±3–10", <= 100 => "±11–100", _ => ">100",
            };
            buckets[bucket] = buckets.GetValueOrDefault(bucket) + 1;
        }
        double agreement = total == 0 ? 0 : (double)exact / total;
        Console.WriteLine($"cost formula validation (Skyrim.esm self-consistent): {exact}/{total} exact " +
            $"({agreement:P2})  " + string.Join("  ", buckets.Select(b => $"{b.Key}:{b.Value}")));
        // Gate at 97%: base Enderal itself ships 4 authored-drift records (BoundSword 92 vs 46,
        // FlamesRightHand 18 vs 16, Flames3 36 vs 31, FlameCloakLeftHand 316 vs 289 — that last
        // is exactly what an earlier MGEF BaseCost of 3.5 yields, later retuned to 3.2 without a
        // recompute). Those are data drift, not formula error; anything beyond them is.
        if (agreement >= 0.97) return true;
        warnings.Add($"COST MODEL DISABLED: formula agreed on only {agreement:P2} of {total} " +
                     "self-consistent base-game spells (<97%); computedAutoCost/costDrift shipped as null");
        Console.Error.WriteLine("!!! COST MODEL DISABLED — see warnings");
        return false;
    }

    /// <summary>Informational: how much REAL drift the modlist carries (override-induced).</summary>
    public void DriftStats(Dataset<SpellDto> spells)
    {
        int total = 0, drifted = 0;
        foreach (var s in spells.Winners)
        {
            var c = s.Cost;
            if (c is null || c.ManualCostCalc || c.CostDrift is null) continue;
            total++;
            if (c.CostDrift != 0) drifted++;
        }
        Console.WriteLine($"cost drift (winner context): {drifted}/{total} auto-calc spells have " +
                          "costDrift ≠ 0 — stored BaseCost no longer matches the live effect data " +
                          "(rebalancing findings, filter costDrift in spells.json)");
    }

    // ---- L3a: every BaseEffect resolves ---------------------------------------------------

    public void BaseEffectResolution(Dataset<SpellDto> spel, Dataset<ScrollDto> scrl,
        Dataset<EnchantmentDto> ench, Dataset<IngestibleDto> alch, Dataset<MagicEffectDto> mgef,
        ModlistLoadOrder lo)
    {
        var dangling = new List<string>();
        void Check(string ds, IEnumerable<(string Fk, List<EffectDto>? Effects)> rows)
        {
            foreach (var (fk, effects) in rows)
                foreach (var e in effects ?? [])
                    if (e.BaseEffect is not null && !mgef.ByKey.ContainsKey(e.BaseEffect.FormKey))
                        dangling.Add($"{ds} {fk} → MGEF {e.BaseEffect.FormKey}");
        }
        Check("SPEL", spel.Winners.Select(s => (s.FormKey, s.Effects)));
        Check("SCRL", scrl.Winners.Select(s => (s.FormKey, s.Effects)));
        Check("ENCH", ench.Winners.Select(s => (s.FormKey, s.Effects)));
        Check("ALCH", alch.Winners.Select(s => (s.FormKey, s.Effects)));
        if (dangling.Count == 0)
        {
            Console.WriteLine("base-effect resolution: PASS (no dangling MGEF links)");
            return;
        }
        warnings.Add($"{dangling.Count} effect entries reference a MGEF absent from the load order " +
                     "(these are REAL dangling links in game): " +
                     string.Join("; ", dangling.Take(20)) + (dangling.Count > 20 ? " …" : ""));
    }

    // ---- L3b: independent raw GRUP scan --------------------------------------------------

    /// <summary>
    /// Counts unique FormKeys per top-level GRUP by walking the plugin bytes directly —
    /// no Mutagen involved — and compares against the projected dataset counts.
    /// Catches "a whole group was silently skipped".
    /// </summary>
    public void RawGrupCrossCheck(ModlistLoadOrder lo, params (string Label, int DatasetCount)[] expected)
    {
        var uniques = expected.ToDictionary(e => e.Label, _ => new HashSet<string>(StringComparer.OrdinalIgnoreCase));
        var wanted = new HashSet<string>(expected.Select(e => e.Label));
        foreach (var entry in lo.Included)
        {
            if (entry.Path is null) continue;
            try { ScanPlugin(entry, wanted, uniques); }
            catch (Exception ex) { warnings.Add($"raw GRUP scan failed on {entry.Name}: {ex.Message}"); }
        }
        foreach (var (label, count) in expected)
        {
            int raw = uniques[label].Count;
            if (raw == count)
                Console.WriteLine($"raw GRUP cross-check {label}: PASS ({raw})");
            else
                warnings.Add($"raw GRUP cross-check {label}: raw scan found {raw} unique FormKeys, " +
                             $"dataset has {count}");
        }
    }

    private static void ScanPlugin(PluginEntry entry, HashSet<string> wanted,
        Dictionary<string, HashSet<string>> uniques)
    {
        var bytes = File.ReadAllBytes(entry.Path!);
        // TES4 header record + its MAST subrecords.
        if (bytes.Length < 24 || !bytes.AsSpan(0, 4).SequenceEqual("TES4"u8)) return;
        uint tes4Size = BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(4));
        var masters = new List<string>();
        int p = 24, end = 24 + (int)tes4Size;
        while (p + 6 <= end)
        {
            string sub = Encoding.ASCII.GetString(bytes, p, 4);
            ushort size = BinaryPrimitives.ReadUInt16LittleEndian(bytes.AsSpan(p + 4));
            if (sub == "MAST")
                masters.Add(Encoding.ASCII.GetString(bytes, p + 6, size).TrimEnd('\0'));
            p += 6 + size;
        }

        // Top-level GRUPs.
        p = end;
        while (p + 24 <= bytes.Length)
        {
            if (!bytes.AsSpan(p, 4).SequenceEqual("GRUP"u8)) break;
            uint groupSize = BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(p + 4));
            string label = Encoding.ASCII.GetString(bytes, p + 8, 4);
            int groupEnd = p + (int)groupSize;
            if (wanted.Contains(label))
            {
                int q = p + 24;
                while (q + 24 <= groupEnd)
                {
                    // records only at this level for the magic groups; skip nested GRUPs defensively
                    if (bytes.AsSpan(q, 4).SequenceEqual("GRUP"u8))
                    {
                        q += (int)BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(q + 4));
                        continue;
                    }
                    uint dataSize = BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(q + 4));
                    uint formId = BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(q + 12));
                    int masterIdx = (int)(formId >> 24);
                    string owner = masterIdx < masters.Count ? masters[masterIdx] : entry.Name;
                    uniques[label].Add($"{formId & 0xFFFFFF:X6}:{owner}");
                    q += 24 + (int)dataSize;
                }
            }
            p = groupEnd;
        }
    }

    // ---- L5: golden fixtures --------------------------------------------------------------

    /// <summary>Asserts golden.json fixtures against the EMITTED files. False = run fails.</summary>
    public bool GoldenFixtures(string outDir)
    {
        var goldenPath = Path.Combine(AppContext.BaseDirectory, "golden.json");
        if (!File.Exists(goldenPath))
        {
            warnings.Add("golden.json not found next to the binary; fixtures skipped");
            return true;
        }
        var root = JsonNode.Parse(File.ReadAllText(goldenPath))!;
        var failures = new List<string>();
        int passed = 0;
        var cache = new Dictionary<string, JsonNode>();
        foreach (var fx in root["fixtures"]!.AsArray())
        {
            string dataset = fx!["dataset"]!.GetValue<string>();
            string formKey = fx["formKey"]!.GetValue<string>();
            string field = fx["field"]!.GetValue<string>();
            string op = fx["op"]!.GetValue<string>();
            var expect = fx["value"];
            string label = $"{dataset} {formKey} {field} {op}" + (expect is null ? "" : $" {expect.ToJsonString()}");

            if (!cache.TryGetValue(dataset, out var doc))
            {
                var file = Path.Combine(outDir, dataset + ".json");
                if (!File.Exists(file)) { failures.Add($"{label}: dataset file missing"); continue; }
                cache[dataset] = doc = JsonNode.Parse(File.ReadAllText(file))!;
            }
            JsonNode? record = doc["records"]!.AsArray()
                .FirstOrDefault(r => r?["formKey"]?.GetValue<string>() == formKey);
            if (record is null) { failures.Add($"{label}: record not found"); continue; }

            JsonNode? node = record;
            foreach (var seg in field.Split('.'))
            {
                if (node is null) break;
                node = int.TryParse(seg, out var idx)
                    ? (node as JsonArray)?[idx]
                    : (node as JsonObject)?.TryGetPropertyValue(seg, out var next) == true ? next : null;
            }

            bool ok = op switch
            {
                "eq" => node is not null && expect is not null &&
                        string.Equals(node.ToJsonString(), expect.ToJsonString(), StringComparison.Ordinal),
                "null" => node is null,
                "nonEmpty" => node is JsonValue v && !string.IsNullOrEmpty(v.ToString()),
                _ => false,
            };
            if (ok) passed++;
            else failures.Add($"{label}: got {(node is null ? "<absent>" : node.ToJsonString())}");
        }
        Console.WriteLine($"golden fixtures: {passed} passed, {failures.Count} failed");
        foreach (var f in failures) Console.Error.WriteLine($"FIXTURE FAIL: {f}");
        return failures.Count == 0;
    }
}
