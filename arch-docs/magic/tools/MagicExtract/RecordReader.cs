using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace MagicExtract;

public sealed record LoadedPlugin(PluginEntry Entry, ModKey Key, ISkyrimModDisposableGetter Mod);

/// <summary>
/// Opens every included plugin as a lazy Mutagen binary overlay under GameRelease.EnderalSE.
///
/// Deliberately does NOT use GameEnvironment / LoadOrder.Import: MO2's VFS means the game Data
/// folder does not contain the mods, so we feed explicit paths and resolve masters ourselves
/// via WithKnownMasters (pass A reads every header first).
///
/// Strings: Enderal's masters are Localized with loose .strings in Stock game/Data/Strings;
/// two mods (Dismembering Framework.esm, Sanguine Symphony.esp) carry theirs inside their own
/// BSA. Per plugin, the strings/BSA root is the directory containing the plugin file.
/// </summary>
public static class RecordReader
{
    public static List<LoadedPlugin> OpenAll(ModlistLoadOrder loadOrder, List<string> warnings)
    {
        var included = loadOrder.Included.Where(e => e.Path is not null).ToList();

        // Pass A: master styles from headers only (cheap), needed so overlays can resolve
        // FormKeys across the whole 300-plugin order including ESL-flagged plugins.
        var styles = new List<KeyedMasterStyle>(included.Count);
        foreach (var entry in included)
        {
            try
            {
                styles.Add(KeyedMasterStyle.FromPath(entry.Path!, GameRelease.EnderalSE));
            }
            catch (Exception ex)
            {
                warnings.Add($"{entry.Name}: master-style read failed: {ex.Message}");
            }
        }
        var styleArr = styles.ToArray();

        // Pass B: full (lazy) overlays.
        var loaded = new List<LoadedPlugin>(included.Count);
        foreach (var entry in included)
        {
            var key = ModKey.FromFileName(entry.Name);
            try
            {
                var dir = Path.GetDirectoryName(entry.Path!)!;
                // .FromPath() lands directly on the final builder in 0.54.4 — the load-order
                // choice stage only exists for separated-master games (Starfield), not Skyrim.
                var builder = SkyrimMod.Create(SkyrimRelease.EnderalSE)
                    .FromPath(new ModPath(key, entry.Path!))
                    .WithKnownMasters(styleArr)
                    .WithBsaFolder(dir)
                    .WithTargetLanguage(Language.English)
                    .ThrowIfUnknownSubrecord(false);
                // Only override the strings folder when it exists: pointing it at a missing dir
                // could shadow the BSA-embedded strings lookup two mods rely on.
                var stringsDir = Path.Combine(dir, "Strings");
                if (Directory.Exists(stringsDir))
                    builder = builder.WithStringsFolder(stringsDir);
                var mod = builder.Construct();
                loaded.Add(new LoadedPlugin(entry, key, mod));
            }
            catch (Exception ex)
            {
                warnings.Add($"{entry.Name}: FAILED to open: {ex.GetType().Name}: {ex.Message}");
            }
        }
        return loaded;
    }

    /// <summary>
    /// Canary 1 — strings. If delocalization is broken every name in the dataset is empty or
    /// a string ID; Enderal's renamed magic schools are the perfect tripwire because they also
    /// prove we read ENDERAL's Skyrim.esm, not vanilla's.
    /// Returns error strings (empty list = pass).
    /// </summary>
    public static List<string> StringsCanary(IReadOnlyDictionary<FormKey, List<(PluginEntry, IActorValueInformationGetter)>> avifChains,
        List<string> warnings)
    {
        var errors = new List<string>();
        var expected = new (uint Id, string Name)[]
        {
            (0x000458, "Mentalism"),    // AVAlteration
            (0x000459, "Entropy"),      // AVConjuration
            (0x00045A, "Elementalism"), // AVDestruction
            (0x00045C, "Light Magic"),  // AVRestoration
        };
        var skyrim = ModKey.FromFileName("Skyrim.esm");
        foreach (var (id, want) in expected)
        {
            var fk = new FormKey(skyrim, id);
            if (!avifChains.TryGetValue(fk, out var chain) || chain.Count == 0)
            {
                errors.Add($"canary AVIF {fk} not found in any plugin");
                continue;
            }
            var name = chain[^1].Item2.Name?.String;
            if (!string.Equals(name, want, StringComparison.Ordinal))
                errors.Add($"canary AVIF {fk}: expected '{want}', got '{name ?? "<null>"}'");
        }
        // AVIllusion 00045B: known to be absent from the serialized reference tree; warn only.
        var ill = new FormKey(skyrim, 0x00045B);
        if (!avifChains.ContainsKey(ill))
            warnings.Add("AVIllusion 00045B:Skyrim.esm not found; using literal 'Psionics' for that school");
        return errors;
    }

    /// <summary>
    /// Canary 2 — BEES. If any included plugin is HEDR &gt; 1.70 the dataset is only correct
    /// while BEES loads those plugins. Fail hard if it's missing/disabled; corroborate with the
    /// runtime log when available.
    /// </summary>
    public static List<string> BeesCanary(ModlistLoadOrder lo, List<string> warnings,
        out int? beesLogEmulatedCount, out DateTime? beesLogTime)
    {
        beesLogEmulatedCount = null;
        beesLogTime = null;
        var errors = new List<string>();
        var needy = lo.Included.Where(e => e.NeedsBees).ToList();
        if (needy.Count == 0) return errors;

        if (!Directory.Exists(lo.BeesModFolder) || !lo.BeesEnabled)
        {
            errors.Add($"{needy.Count} enabled plugins have HEDR > 1.70 and would NOT load without " +
                       "BEES (Backported Extended ESL Support), which is missing or disabled. " +
                       "Refusing to emit a dataset that mislabels their records as winning.");
            return errors;
        }

        // Corroboration: BEES logs to the SKYRIM SE documents folder (not Enderal's).
        var log = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
            "My Games", "Skyrim Special Edition", "SKSE", "BackportedESLSupport.log");
        if (File.Exists(log))
        {
            try
            {
                var emulated = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (var line in File.ReadLines(log))
                {
                    const string marker = "Emulated old header version for ";
                    int idx = line.IndexOf(marker, StringComparison.Ordinal);
                    if (idx >= 0)
                        emulated.Add(line.Substring(idx + marker.Length).TrimEnd('.'));
                }
                beesLogEmulatedCount = emulated.Count;
                beesLogTime = File.GetLastWriteTime(log);
                foreach (var e in needy)
                    if (!emulated.Contains(e.Name))
                        warnings.Add($"{e.Name}: HEDR > 1.70 but absent from the BEES log " +
                                     "(log may predate this plugin; launch the game to refresh)");
            }
            catch (Exception ex)
            {
                warnings.Add($"BEES log parse failed: {ex.Message}");
            }
        }
        else
        {
            warnings.Add("BEES runtime log not found (game not launched since install?); " +
                         "presence check passed, runtime corroboration unavailable");
        }
        return errors;
    }
}
