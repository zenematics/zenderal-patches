using System.Text;

namespace MagicExtract;

/// <summary>One plugin in the effective load order (or excluded from it, with a reason).</summary>
public sealed record PluginEntry
{
    public required string Name { get; init; }
    public required int LoadOrderIndex { get; init; }
    public required bool Enabled { get; init; }
    public string? Path { get; init; }
    /// <summary>HEDR version float at offset 30 of the TES4 record; null if unreadable.</summary>
    public float? HeaderVersion { get; init; }
    /// <summary>True when the plugin loads only because BEES emulates its 1.71 header.</summary>
    public bool NeedsBees => HeaderVersion is > 1.705f;
    /// <summary>Null when included; otherwise why the plugin is not part of resolution.</summary>
    public string? ExclusionReason { get; init; }
    public bool Included => ExclusionReason is null;
}

/// <summary>
/// Builds the effective load order from an MO2 portable-instance profile.
///
/// MO2 has TWO orderings and mixing them is the classic error:
///   - modlist.txt   = FILE priority only (which copy of Foo.esp wins on disk).
///                     First line is HIGHEST priority, so iterate REVERSED so later
///                     registrations overwrite earlier ones.
///   - loadorder.txt = RECORD priority only (which plugin's records win). Index 0 = lowest.
/// plugins.txt supplies enablement ('*' prefix); the five implicit masters are absent
/// from it by design and are always enabled.
///
/// No form-version filter: this list ships BEES (Backported Extended ESL Support), which
/// makes SSE 1.5.97 load HEDR-1.71 plugins. We still RECORD each version so the BEES
/// dependency is auditable per plugin.
/// </summary>
public sealed class ModlistLoadOrder
{
    private static readonly string[] PluginExtensions = [".esp", ".esm", ".esl"];
    private static readonly string[] ImplicitMasters =
    [
        "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm",
        "Enderal - Forgotten Stories.esm",
    ];

    public required IReadOnlyList<PluginEntry> Entries { get; init; }
    public required List<string> Warnings { get; init; }
    public required string BeesModFolder { get; init; }
    public bool BeesEnabled { get; init; }

    public IEnumerable<PluginEntry> Included => Entries.Where(e => e.Included);
    public bool RequiresBees => Included.Any(e => e.NeedsBees);

    public static ModlistLoadOrder Build(string modlistRoot, string profileName, string gameDataDir)
    {
        var warnings = new List<string>();
        string profileDir = Path.Combine(modlistRoot, "profiles", profileName);
        string modsDir = Path.Combine(modlistRoot, "mods");
        if (!Directory.Exists(profileDir))
            throw new DirectoryNotFoundException($"MO2 profile not found: {profileDir}");

        // ---- file-priority index: plugin filename -> winning path -------------------
        // Base layer: the game Data dir (Stock game).
        var paths = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        RegisterPlugins(paths, gameDataDir);

        // Mods, reversed: modlist.txt first line = highest priority, so iterating the file
        // bottom-up and letting later registrations overwrite yields the MO2 winner.
        bool beesEnabled = false;
        var modlistLines = File.ReadAllLines(Path.Combine(profileDir, "modlist.txt"));
        foreach (var raw in modlistLines.Reverse())
        {
            var line = raw.Trim();
            if (line.Length == 0 || line[0] == '#') continue;
            if (line[0] != '+') // '-' disabled, '*_separator' etc.
            {
                if (line.Length > 1 && line[0] == '-' &&
                    line.Substring(1).Equals("Backported Extended ESL Support", StringComparison.OrdinalIgnoreCase))
                    warnings.Add("BEES mod folder exists but is DISABLED in modlist.txt");
                continue;
            }
            var modName = line.Substring(1);
            if (modName.EndsWith("_separator", StringComparison.OrdinalIgnoreCase)) continue;
            if (modName.Equals("Backported Extended ESL Support", StringComparison.OrdinalIgnoreCase))
                beesEnabled = true;
            var modDir = Path.Combine(modsDir, modName);
            RegisterPlugins(paths, modDir);
            RegisterPlugins(paths, Path.Combine(modDir, "Data")); // some mods nest a Data/ layer
        }

        // MO2 overwrite/ beats everything.
        RegisterPlugins(paths, Path.Combine(modlistRoot, "overwrite"));

        // ---- enablement --------------------------------------------------------------
        var enabled = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var raw in File.ReadAllLines(Path.Combine(profileDir, "plugins.txt")))
        {
            var line = raw.Trim();
            if (line.StartsWith('*')) enabled.Add(line.Substring(1));
        }
        foreach (var m in ImplicitMasters) enabled.Add(m); // absent from plugins.txt by design

        // ---- record priority ----------------------------------------------------------
        var loadorder = File.ReadAllLines(Path.Combine(profileDir, "loadorder.txt"))
            .Select(l => l.Trim())
            .Where(l => l.Length > 0 && l[0] != '#')
            .ToList();

        var entries = new List<PluginEntry>(loadorder.Count);
        for (int i = 0; i < loadorder.Count; i++)
        {
            var name = loadorder[i];
            bool isEnabled = enabled.Contains(name);
            paths.TryGetValue(name, out var path);
            float? version = path is null ? null : TryReadHeaderVersion(path, warnings);

            string? exclusion = null;
            if (!isEnabled) exclusion = "disabled in plugins.txt";
            else if (path is null) exclusion = "file not found in any enabled mod folder";
            else if (version is null) warnings.Add($"{name}: could not read HEDR version; including anyway");

            if (exclusion is not null && isEnabled)
                warnings.Add($"{name}: enabled in plugins.txt but {exclusion}");

            entries.Add(new PluginEntry
            {
                Name = name,
                LoadOrderIndex = i,
                Enabled = isEnabled,
                Path = path,
                HeaderVersion = version,
                ExclusionReason = exclusion,
            });
        }

        // Plugins that exist on disk & are enabled but missing from loadorder.txt would be
        // a profile inconsistency worth knowing about.
        var inLoadorder = new HashSet<string>(loadorder, StringComparer.OrdinalIgnoreCase);
        foreach (var name in enabled)
            if (!inLoadorder.Contains(name))
                warnings.Add($"{name}: enabled in plugins.txt but missing from loadorder.txt");

        return new ModlistLoadOrder
        {
            Entries = entries,
            Warnings = warnings,
            BeesModFolder = Path.Combine(modsDir, "Backported Extended ESL Support"),
            BeesEnabled = beesEnabled,
        };
    }

    private static void RegisterPlugins(Dictionary<string, string> paths, string dir)
    {
        if (!Directory.Exists(dir)) return;
        foreach (var file in Directory.EnumerateFiles(dir))
        {
            var ext = Path.GetExtension(file);
            if (PluginExtensions.Contains(ext, StringComparer.OrdinalIgnoreCase))
                paths[Path.GetFileName(file)] = file;
        }
    }

    /// <summary>HEDR version = float at absolute file offset 30 (TES4 header, first subrecord).</summary>
    private static float? TryReadHeaderVersion(string path, List<string> warnings)
    {
        try
        {
            Span<byte> buf = stackalloc byte[40];
            using var fs = File.OpenRead(path);
            if (fs.Read(buf) < 40) return null;
            // Sanity: file must start with TES4 and offset 24 must be the HEDR subrecord.
            if (!buf.Slice(0, 4).SequenceEqual("TES4"u8)) { warnings.Add($"{path}: no TES4 magic"); return null; }
            if (!buf.Slice(24, 4).SequenceEqual("HEDR"u8)) { warnings.Add($"{path}: HEDR not at offset 24"); return null; }
            return BitConverter.ToSingle(buf.Slice(30, 4));
        }
        catch (Exception ex)
        {
            warnings.Add($"{path}: header read failed: {ex.Message}");
            return null;
        }
    }
}
