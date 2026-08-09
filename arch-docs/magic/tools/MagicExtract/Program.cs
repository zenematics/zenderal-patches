using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

namespace MagicExtract;

public static class Program
{
    public static int Main(string[] args)
    {
        string? modlistRoot = null, profile = null, gameData = null, outDir = null, reportsDir = null;
        bool probeOnly = false;
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--modlist-root": modlistRoot = args[++i]; break;
                case "--profile": profile = args[++i]; break;
                case "--game-data": gameData = args[++i]; break;
                case "--out": outDir = args[++i]; break;
                case "--reports": reportsDir = args[++i]; break;
                case "--probe": probeOnly = true; break;
                default:
                    Console.Error.WriteLine($"unknown arg: {args[i]}");
                    return 2;
            }
        }
        if (modlistRoot is null || profile is null || gameData is null)
        {
            Console.Error.WriteLine("usage: MagicExtract --modlist-root <dir> --profile <name> --game-data <dir> " +
                                    "[--out <dir> --reports <dir>] [--probe]");
            return 2;
        }
        if (!probeOnly && (outDir is null || reportsDir is null))
        {
            Console.Error.WriteLine("--out and --reports are required unless --probe");
            return 2;
        }

        var warnings = new List<string>();

        // ---- load order -------------------------------------------------------------
        var lo = ModlistLoadOrder.Build(modlistRoot, profile, gameData);
        warnings.AddRange(lo.Warnings);
        var included = lo.Included.ToList();
        int needsBees = included.Count(e => e.NeedsBees);
        Console.WriteLine($"load order: {lo.Entries.Count} entries, {included.Count} included, " +
                          $"{lo.Entries.Count(e => !e.Included)} excluded, {needsBees} require BEES");

        // ---- canary 2: BEES ----------------------------------------------------------
        var beesErrors = RecordReader.BeesCanary(lo, warnings, out var beesCount, out var beesTime);
        if (beesErrors.Count > 0)
        {
            foreach (var e in beesErrors) Console.Error.WriteLine($"FATAL: {e}");
            return 1;
        }
        if (beesCount is not null)
            Console.WriteLine($"BEES log: {beesCount} plugins emulated, log mtime {beesTime:yyyy-MM-dd HH:mm}");

        // ---- open plugins --------------------------------------------------------------
        var loaded = RecordReader.OpenAll(lo, warnings);
        Console.WriteLine($"opened {loaded.Count}/{included.Count} plugins");

        try
        {
            // ---- canary 1: strings (needs AVIF chains) ----------------------------------
            var avifChains = Chains.Build(loaded, m => m.ActorValueInformation);
            var stringErrors = RecordReader.StringsCanary(avifChains, warnings);
            if (stringErrors.Count > 0)
            {
                foreach (var e in stringErrors) Console.Error.WriteLine($"FATAL: {e}");
                Console.Error.WriteLine("String delocalization is broken; refusing to emit a nameless dataset.");
                return 1;
            }
            Console.WriteLine("strings canary: PASS (Mentalism / Entropy / Elementalism / Light Magic)");

            if (probeOnly)
            {
                Probe(loaded);
                PrintWarnings(warnings);
                return 0;
            }

            var ok = Extractor.Run(loaded, lo, outDir!, reportsDir!,
                beesCount, beesTime, warnings);
            PrintWarnings(warnings);
            return ok ? 0 : 1;
        }
        finally
        {
            foreach (var lp in loaded) lp.Mod.Dispose();
        }
    }

    /// <summary>Per-plugin magic record counts + HEDR versions; the go/no-go for the design.</summary>
    private static void Probe(List<LoadedPlugin> loaded)
    {
        Console.WriteLine();
        Console.WriteLine($"{"plugin",-55} {"HEDR",5} {"SPEL",5} {"MGEF",5} {"ENCH",5} {"SCRL",5} {"ALCH",5} {"SHOU",5}");
        foreach (var lp in loaded)
        {
            int spel = lp.Mod.Spells.Count, mgef = lp.Mod.MagicEffects.Count,
                ench = lp.Mod.ObjectEffects.Count, scrl = lp.Mod.Scrolls.Count,
                alch = lp.Mod.Ingestibles.Count, shou = lp.Mod.Shouts.Count;
            if (spel + mgef + ench + scrl + alch + shou == 0) continue;
            Console.WriteLine($"{lp.Entry.Name,-55} {lp.Entry.HeaderVersion,5:0.00} {spel,5} {mgef,5} {ench,5} {scrl,5} {alch,5} {shou,5}");
        }
    }

    private static void PrintWarnings(List<string> warnings)
    {
        if (warnings.Count == 0) return;
        Console.WriteLine();
        Console.WriteLine($"--- {warnings.Count} warnings ---");
        foreach (var w in warnings) Console.WriteLine($"  warn: {w}");
    }
}

/// <summary>FormKey -> full override chain in load order (last element wins).</summary>
public static class Chains
{
    public static Dictionary<FormKey, List<(PluginEntry, TGetter)>> Build<TGetter>(
        IEnumerable<LoadedPlugin> loaded,
        Func<ISkyrimModGetter, IReadOnlyCollection<TGetter>> group)
        where TGetter : class, ISkyrimMajorRecordGetter
    {
        var chains = new Dictionary<FormKey, List<(PluginEntry, TGetter)>>();
        foreach (var lp in loaded) // loaded is already in load order; index 0 = lowest priority
        {
            foreach (var rec in group(lp.Mod))
            {
                if (!chains.TryGetValue(rec.FormKey, out var chain))
                    chains[rec.FormKey] = chain = new List<(PluginEntry, TGetter)>(1);
                chain.Add((lp.Entry, rec));
            }
        }
        return chains;
    }
}
