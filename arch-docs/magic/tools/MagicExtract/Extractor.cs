using System.Text.Json.Nodes;
using MagicExtract.Projections;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace MagicExtract;

/// <summary>One projected dataset: winning DTOs + full chain snapshots for provenance.</summary>
public sealed class Dataset<TDto> where TDto : class, IRecordDto
{
    public required string Name { get; init; }         // file stem, e.g. "spells"
    public required string RecordType { get; init; }   // GRUP label, e.g. "SPEL"
    public required List<TDto> Winners { get; init; }  // sorted by FormKey
    /// <summary>FormKey → [(plugin, snapshot DTO)] for chains longer than one.</summary>
    public required Dictionary<string, List<(string Plugin, TDto Dto)>> ChainSnapshots { get; init; }
    /// <summary>FormKey → human-readable "field: before → after" strings for the conflicts report.</summary>
    public Dictionary<string, List<string>> ChangeDisplays { get; } = new();
    public Dictionary<string, TDto> ByKey { get; } = new();
}

public static class Extractor
{
    private static readonly HashSet<string> ImplicitMasters = new(StringComparer.OrdinalIgnoreCase)
    {
        "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm",
        "Enderal - Forgotten Stories.esm",
    };

    public static bool Run(List<LoadedPlugin> loaded, ModlistLoadOrder lo,
        string outDir, string reportsDir,
        int? beesLogEmulatedCount, DateTime? beesLogTime, List<string> warnings)
    {
        // ---- chains for every group we either emit or resolve names from -----------------
        Console.WriteLine("building override chains...");
        var mgefChains = Chains.Build(loaded, m => m.MagicEffects);
        var spelChains = Chains.Build(loaded, m => m.Spells);
        var enchChains = Chains.Build(loaded, m => m.ObjectEffects);
        var scrlChains = Chains.Build(loaded, m => m.Scrolls);
        var alchChains = Chains.Build(loaded, m => m.Ingestibles);
        var shouChains = Chains.Build(loaded, m => m.Shouts);
        var woopChains = Chains.Build(loaded, m => m.WordsOfPower);
        var lvspChains = Chains.Build(loaded, m => m.LeveledSpells);
        var gmstChains = Chains.Build(loaded, m => m.GameSettings);
        var avifChains = Chains.Build(loaded, m => m.ActorValueInformation);
        var perkChains = Chains.Build(loaded, m => m.Perks);
        var kywdChains = Chains.Build(loaded, m => m.Keywords);
        var projChains = Chains.Build(loaded, m => m.Projectiles);
        var equpChains = Chains.Build(loaded, m => m.EquipTypes);
        var explChains = Chains.Build(loaded, m => m.Explosions);
        var globChains = Chains.Build(loaded, m => m.Globals);
        var raceChains = Chains.Build(loaded, m => m.Races);
        var bookChains = Chains.Build(loaded, m => m.Books); // for taughtBy — not emitted as a dataset

        var names = new NameIndex();
        names.Add(mgefChains); names.Add(spelChains); names.Add(enchChains); names.Add(scrlChains);
        names.Add(alchChains); names.Add(shouChains); names.Add(woopChains); names.Add(lvspChains);
        names.Add(avifChains); names.Add(perkChains); names.Add(kywdChains); names.Add(projChains);
        names.Add(equpChains); names.Add(explChains); names.Add(globChains); names.Add(raceChains);

        var winningMgef = mgefChains.ToDictionary(kv => kv.Key, kv => kv.Value[^1].Item2);
        var schoolNames = SchoolNames(avifChains, warnings);

        // ---- project ----------------------------------------------------------------------
        Console.WriteLine("projecting records...");
        var mgefDs = Project(mgefChains, "magic-effects", "MGEF", m => Builders.MagicEffect(m, names));
        var spelDs = Project(spelChains, "spells", "SPEL", s => Builders.Spell(s, names, winningMgef, schoolNames));
        var enchDs = Project(enchChains, "enchantments", "ENCH", e => Builders.Enchantment(e, names, winningMgef));
        var scrlDs = Project(scrlChains, "scrolls", "SCRL", s => Builders.Scroll(s, names, winningMgef));
        var alchDs = Project(alchChains, "ingestibles", "ALCH", a => Builders.Ingestible(a, names, winningMgef));
        var shouDs = Project(shouChains, "shouts", "SHOU", s => Builders.Shout(s, names));
        var lvspDs = Project(lvspChains, "leveled-spells", "LVSP", l => Builders.LeveledSpell(l, names));
        var gmstDs = Project(gmstChains, "game-settings", "GMST", Builders.GameSetting);

        // usedBy/taughtBy AFTER diffing, so they never appear as changed fields.
        FillUsedBy(mgefDs, spelDs, scrlDs, enchDs, alchDs);
        FillTaughtBy(spelDs, bookChains);

        // ---- self-checks -------------------------------------------------------------------
        var check = new SelfCheck(warnings);
        bool costModelOk = check.FormulaValidation(loaded);
        if (!costModelOk)
        {
            foreach (var s in spelDs.Winners) NullCost(s.Cost);
            foreach (var s in scrlDs.Winners) NullCost(s.Cost);
        }
        else check.DriftStats(spelDs);
        check.BaseEffectResolution(spelDs, scrlDs, enchDs, alchDs, mgefDs, lo);
        check.RawGrupCrossCheck(lo,
            ("SPEL", spelDs.Winners.Count), ("MGEF", mgefDs.Winners.Count),
            ("ENCH", enchDs.Winners.Count), ("SCRL", scrlDs.Winners.Count),
            ("ALCH", alchDs.Winners.Count), ("SHOU", shouDs.Winners.Count),
            ("LVSP", lvspDs.Winners.Count));

        // ---- emit ---------------------------------------------------------------------------
        Console.WriteLine("emitting JSON...");
        Emit(outDir, mgefDs); Emit(outDir, spelDs); Emit(outDir, enchDs); Emit(outDir, scrlDs);
        Emit(outDir, alchDs); Emit(outDir, shouDs); Emit(outDir, lvspDs); Emit(outDir, gmstDs);

        EmitLookups(outDir, names, perkChains, kywdChains, projChains, equpChains, avifChains, schoolNames, gmstDs);
        EmitLoadOrder(outDir, lo);
        EmitProvenance(outDir, mgefDs, spelDs, enchDs, scrlDs, alchDs, shouDs, lvspDs, gmstDs);
        Reports.SpellsCsv(Path.Combine(outDir, "spells.csv"), spelDs);
        Reports.ScrollsCsv(Path.Combine(outDir, "scrolls.csv"), scrlDs);
        Reports.EnchantmentsCsv(Path.Combine(outDir, "enchantments.csv"), enchDs);
        Reports.Overview(Path.Combine(reportsDir, "magic-overview.md"), lo, spelDs, mgefDs, enchDs,
            scrlDs, alchDs, shouDs, lvspDs, gmstDs, schoolNames, costModelOk, beesLogEmulatedCount, beesLogTime);
        Reports.Conflicts(Path.Combine(reportsDir, "magic-conflicts.md"),
            new IConflictSource[] { spelDs.AsConflicts(), mgefDs.AsConflicts(), enchDs.AsConflicts(),
                scrlDs.AsConflicts(), alchDs.AsConflicts(), shouDs.AsConflicts(), lvspDs.AsConflicts() });

        // golden fixtures LAST, against the emitted files.
        bool goldenOk = check.GoldenFixtures(outDir);

        Json.WriteFile(Path.Combine(outDir, "manifest.json"), new
        {
            schemaVersion = 1,
            generatedBy = "MagicExtract (Mutagen.Bethesda.Skyrim 0.54.4, read-only)",
            extractedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            requiresBees = lo.RequiresBees,
            beesLogEmulatedCount,
            beesLogTime = beesLogTime?.ToString("yyyy-MM-dd HH:mm:ss"),
            costModelEnabled = costModelOk,
            counts = new Dictionary<string, int>
            {
                ["spells"] = spelDs.Winners.Count,
                ["magicEffects"] = mgefDs.Winners.Count,
                ["enchantments"] = enchDs.Winners.Count,
                ["scrolls"] = scrlDs.Winners.Count,
                ["ingestibles"] = alchDs.Winners.Count,
                ["shouts"] = shouDs.Winners.Count,
                ["leveledSpells"] = lvspDs.Winners.Count,
                ["gameSettings"] = gmstDs.Winners.Count,
            },
            warnings,
        });

        Console.WriteLine($"done: {spelDs.Winners.Count} spells, {mgefDs.Winners.Count} magic effects, " +
                          $"{enchDs.Winners.Count} enchantments, {scrlDs.Winners.Count} scrolls, " +
                          $"{alchDs.Winners.Count} ingestibles, {shouDs.Winners.Count} shouts, " +
                          $"{gmstDs.Winners.Count} game settings");
        return goldenOk;
    }

    private static void NullCost(CostDto? c)
    {
        if (c is null) return;
        c.ComputedAutoCost = null; c.CostDrift = null; c.CostMatchesStored = null;
    }

    // ---- dataset projection with provenance + per-field diff ---------------------------------

    private static Dataset<TDto> Project<TGetter, TDto>(
        Dictionary<FormKey, List<(PluginEntry, TGetter)>> chains,
        string name, string recordType, Func<TGetter, TDto> project)
        where TGetter : class, ISkyrimMajorRecordGetter
        where TDto : class, IRecordDto
    {
        var winners = new List<TDto>(chains.Count);
        var snapshots = new Dictionary<string, List<(string, TDto)>>();
        var displaysByKey = new Dictionary<string, List<string>>();
        foreach (var (fk, chain) in chains)
        {
            var (winEntry, winRec) = chain[^1];
            var dto = project(winRec);
            string definedIn = fk.ModKey.FileName;
            var prov = new ProvenanceDto
            {
                DefinedIn = definedIn,
                // "new" = added by a modlist plugin, not shipped by a base master. Base-master
                // records trivially have owner == chain[0]; that is not what "new" means here.
                IsNewRecord = !ImplicitMasters.Contains(definedIn)
                              && chain[0].Item1.Name.Equals(definedIn, StringComparison.OrdinalIgnoreCase),
                IsInjected = !chain.Any(c => c.Item1.Name.Equals(definedIn, StringComparison.OrdinalIgnoreCase)),
                Winner = winEntry.Name,
                WinnerLoadOrderIndex = winEntry.LoadOrderIndex,
                Chain = chain.Select(c => c.Item1.Name).ToList(),
                WinnerHeaderVersion = winEntry.HeaderVersion is { } v ? (float)Math.Round(v, 2) : null,
                WinnerNeedsBees = winEntry.NeedsBees,
            };

            List<string>? displays = null;
            if (chain.Count > 1)
            {
                var chainDtos = chain.Select(c => (c.Item1.Name, project(c.Item2))).ToList();
                (prov.ChangedFields, displays) = DiffFields(chainDtos[0].Item2, dto);
                snapshots[fk.ToString()] = chainDtos;
            }
            dto.Provenance = prov;
            winners.Add(dto);
            if (displays is not null) displaysByKey[fk.ToString()] = displays;
        }
        winners.Sort((a, b) => string.CompareOrdinal(a.FormKey, b.FormKey));
        var ds = new Dataset<TDto> { Name = name, RecordType = recordType, Winners = winners, ChainSnapshots = snapshots };
        foreach (var w in winners) ds.ByKey[w.FormKey] = w;
        foreach (var (k, v) in displaysByKey) ds.ChangeDisplays[k] = v;
        return ds;
    }

    /// <summary>Top-level DTO fields whose JSON differs between first carrier and winner.</summary>
    private static (List<string>? Names, List<string>? Displays) DiffFields<TDto>(TDto baseDto, TDto winnerDto)
        where TDto : class, IRecordDto
    {
        var a = Json.ToNode(baseDto);
        var b = Json.ToNode(winnerDto);
        a.Remove("provenance"); b.Remove("provenance");
        var keys = a.Select(kv => kv.Key).Union(b.Select(kv => kv.Key)).ToList();
        List<string>? changed = null;
        List<string>? displays = null;
        foreach (var k in keys)
        {
            var an = a.TryGetPropertyValue(k, out var x) ? x : null;
            var bn = b.TryGetPropertyValue(k, out var y) ? y : null;
            if (string.Equals(an?.ToJsonString(), bn?.ToJsonString(), StringComparison.Ordinal)) continue;
            (changed ??= new List<string>()).Add(k);
            (displays ??= new List<string>()).AddRange(Display(k, an, bn));
        }
        return (changed, displays);
    }

    /// <summary>"field: before → after" for primitives; one level into objects; bare name otherwise.</summary>
    private static IEnumerable<string> Display(string key, JsonNode? a, JsonNode? b)
    {
        static string P(JsonNode? n) => n is null ? "∅" : n is JsonValue ? n.ToJsonString() : "…";
        if (a is JsonObject ao && b is JsonObject bo)
        {
            var subs = new List<string>();
            foreach (var sk in ao.Select(kv => kv.Key).Union(bo.Select(kv => kv.Key)))
            {
                var av = ao.TryGetPropertyValue(sk, out var x) ? x : null;
                var bv = bo.TryGetPropertyValue(sk, out var y) ? y : null;
                if (string.Equals(av?.ToJsonString(), bv?.ToJsonString(), StringComparison.Ordinal)) continue;
                if (av is JsonValue or null && bv is JsonValue or null)
                    subs.Add($"{key}.{sk}: {P(av)} → {P(bv)}");
                else
                    subs.Add($"{key}.{sk}");
            }
            if (subs.Count > 0) return subs;
        }
        if (a is JsonValue or null && b is JsonValue or null)
            return [$"{key}: {P(a)} → {P(b)}"];
        return [key];
    }

    private static void FillUsedBy(Dataset<MagicEffectDto> mgef, Dataset<SpellDto> spel,
        Dataset<ScrollDto> scrl, Dataset<EnchantmentDto> ench, Dataset<IngestibleDto> alch)
    {
        static List<string> Add(List<string>? list, string key)
        {
            list ??= new List<string>();
            if (list.Count == 0 || list[^1] != key) list.Add(key); // sources iterate sorted; dedupe adjacents
            return list;
        }
        void Collect(IEnumerable<(string FormKey, List<EffectDto>? Effects)> src, Action<UsedByDto, string> add)
        {
            foreach (var (fk, effects) in src)
            {
                if (effects is null) continue;
                foreach (var e in effects)
                {
                    if (e.BaseEffect is null) continue;
                    if (!mgef.ByKey.TryGetValue(e.BaseEffect.FormKey, out var m)) continue;
                    add(m.UsedBy ??= new UsedByDto(), fk);
                }
            }
        }
        Collect(spel.Winners.Select(s => (s.FormKey, s.Effects)), (u, k) => u.Spells = Add(u.Spells, k));
        Collect(scrl.Winners.Select(s => (s.FormKey, s.Effects)), (u, k) => u.Scrolls = Add(u.Scrolls, k));
        Collect(ench.Winners.Select(s => (s.FormKey, s.Effects)), (u, k) => u.Enchantments = Add(u.Enchantments, k));
        Collect(alch.Winners.Select(s => (s.FormKey, s.Effects)), (u, k) => u.Ingestibles = Add(u.Ingestibles, k));
    }

    /// <summary>Mark every spell some winning Book record teaches — the player-obtainable set.
    /// Enderal's _01E_SpellBook* Books use the standard Teaches/BookSpell field, as do
    /// third-party spell packs, so this is ground truth rather than an EditorID heuristic.
    /// Spells granted only by scripts/quests are not caught and stay untagged.</summary>
    private static void FillTaughtBy(Dataset<SpellDto> spel,
        Dictionary<FormKey, List<(PluginEntry, IBookGetter)>> bookChains)
    {
        foreach (var (fk, chain) in bookChains)
        {
            var book = chain[^1].Item2;
            if (book.Teaches is not IBookSpellGetter t || t.Spell.FormKey.IsNull) continue;
            if (!spel.ByKey.TryGetValue(t.Spell.FormKey.ToString(), out var s)) continue;
            (s.TaughtBy ??= new List<RefDto>()).Add(new RefDto
            {
                FormKey = fk.ToString(),
                EditorId = book.EditorID,
                Name = book.Name?.String,
            });
        }
        foreach (var s in spel.Winners)
            s.TaughtBy?.Sort((a, b) => string.CompareOrdinal(a.FormKey, b.FormKey));
    }

    private static Dictionary<ActorValue, string> SchoolNames(
        Dictionary<FormKey, List<(PluginEntry, IActorValueInformationGetter)>> avifChains, List<string> warnings)
    {
        var skyrim = ModKey.FromFileName("Skyrim.esm");
        var map = new Dictionary<ActorValue, string>();
        void Set(ActorValue av, uint id, string fallback)
        {
            var fk = new FormKey(skyrim, id);
            string? n = avifChains.TryGetValue(fk, out var chain) ? chain[^1].Item2.Name?.String : null;
            map[av] = string.IsNullOrEmpty(n) ? fallback : n!;
        }
        Set(ActorValue.Alteration, 0x000458, "Mentalism");
        Set(ActorValue.Conjuration, 0x000459, "Entropy");
        Set(ActorValue.Destruction, 0x00045A, "Elementalism");
        Set(ActorValue.Illusion, 0x00045B, "Psionics");
        Set(ActorValue.Restoration, 0x00045C, "Light Magic");
        return map;
    }

    // ---- emit helpers -----------------------------------------------------------------------

    private static void Emit<TDto>(string outDir, Dataset<TDto> ds) where TDto : class, IRecordDto
        => Json.WriteFile(Path.Combine(outDir, ds.Name + ".json"),
            new { schemaVersion = 1, recordType = ds.RecordType, records = ds.Winners });

    private static void EmitLookups(string outDir, NameIndex names,
        Dictionary<FormKey, List<(PluginEntry, IPerkGetter)>> perks,
        Dictionary<FormKey, List<(PluginEntry, IKeywordGetter)>> keywords,
        Dictionary<FormKey, List<(PluginEntry, IProjectileGetter)>> projectiles,
        Dictionary<FormKey, List<(PluginEntry, IEquipTypeGetter)>> equipTypes,
        Dictionary<FormKey, List<(PluginEntry, IActorValueInformationGetter)>> avif,
        Dictionary<ActorValue, string> schoolNames,
        Dataset<GameSettingDto> gmst)
    {
        static List<object> Table<T>(Dictionary<FormKey, List<(PluginEntry, T)>> chains)
            where T : class, ISkyrimMajorRecordGetter
            => chains
                .OrderBy(kv => kv.Key.ToString(), StringComparer.Ordinal)
                .Select(kv =>
                {
                    var w = kv.Value[^1].Item2;
                    return (object)new
                    {
                        formKey = kv.Key.ToString(),
                        editorId = w.EditorID,
                        name = w is Mutagen.Bethesda.Plugins.Aspects.INamedGetter n ? n.Name : null,
                        winner = kv.Value[^1].Item1.Name,
                    };
                })
                .ToList();

        var costModel = CostModel(gmst);
        Json.WriteFile(Path.Combine(outDir, "lookups.json"), new
        {
            schemaVersion = 1,
            schools = schoolNames.OrderBy(kv => kv.Key.ToString()).Select(kv => new
            {
                actorValue = kv.Key.ToString(),
                displayName = kv.Value,
            }),
            costModel,
            perks = Table(perks),
            keywords = Table(keywords),
            projectiles = Table(projectiles),
            equipTypes = Table(equipTypes),
            actorValueInformation = Table(avif),
        });
    }

    private static object CostModel(Dataset<GameSettingDto> gmst)
    {
        double? Get(string editorId) =>
            gmst.Winners.FirstOrDefault(g => string.Equals(g.EditorId, editorId, StringComparison.OrdinalIgnoreCase))
                ?.Value is { } v ? Convert.ToDouble(v) : null;
        double mult = Get("fMagicCasterSkillCostMult") ?? 0.5;
        double scale = Get("fMagicSkillCostScale") ?? 0.5;
        double dual = Get("fMagicDualCastingCostMult") ?? 2.8;
        var curve = new[] { 0, 25, 50, 75, 100 }.Select(skill => new
        {
            skill,
            multiplier = Math.Round(1.0 - mult * Math.Pow(skill * 0.0025, scale), 4),
        });
        return new
        {
            confidence = "approximate",
            note = "skillMultiplier ≈ 1 − fMagicCasterSkillCostMult × (skill × 0.0025)^fMagicSkillCostScale. " +
                   "The 0.0025 (=1/400) constant is engine-side, not a GMST in this load order. " +
                   "Everything past baseCost is runtime- and perk-dependent.",
            fMagicCasterSkillCostMult = mult,
            fMagicSkillCostScale = scale,
            fMagicDualCastingCostMult = dual,
            skillCurve = curve,
        };
    }

    private static void EmitLoadOrder(string outDir, ModlistLoadOrder lo)
    {
        Json.WriteFile(Path.Combine(outDir, "load-order.json"), new
        {
            schemaVersion = 1,
            requiresBees = lo.RequiresBees,
            pluginsRequiringBees = lo.Included.Count(e => e.NeedsBees),
            plugins = lo.Entries.Select(e => new
            {
                name = e.Name,
                index = e.LoadOrderIndex,
                enabled = e.Enabled,
                headerVersion = e.HeaderVersion is { } v ? (float?)Math.Round(v, 2) : null,
                needsBees = e.NeedsBees ? (bool?)true : null,
                exclusionReason = e.ExclusionReason,
                // mod folder name, not the machine-specific absolute path
                source = e.Path is null ? null
                    : Path.GetFileName(Path.GetDirectoryName(e.Path)) is "Data" ? "Stock game/Data"
                    : Path.GetFileName(Path.GetDirectoryName(e.Path)),
            }),
        });
    }

    private static void EmitProvenance(string outDir, params object[] datasets)
    {
        var all = new SortedDictionary<string, object>(StringComparer.Ordinal);
        foreach (var dsObj in datasets)
        {
            // each is Dataset<TDto>; use dynamic-free reflection over the known property
            var t = dsObj.GetType();
            var name = (string)t.GetProperty("Name")!.GetValue(dsObj)!;
            var snaps = (System.Collections.IDictionary)t.GetProperty("ChainSnapshots")!.GetValue(dsObj)!;
            foreach (System.Collections.DictionaryEntry kv in snaps)
            {
                var list = (System.Collections.IEnumerable)kv.Value!;
                var chain = new List<object>();
                foreach (var item in list)
                {
                    var it = item.GetType();
                    chain.Add(new
                    {
                        plugin = it.GetField("Item1")!.GetValue(item),
                        record = it.GetField("Item2")!.GetValue(item),
                    });
                }
                all[(string)kv.Key!] = new { dataset = name, chain };
            }
        }
        Json.WriteFile(Path.Combine(outDir, ".provenance.json"), all);
    }
}

/// <summary>Type-erased view of a dataset for the conflicts report.</summary>
public interface IConflictSource
{
    string Name { get; }
    IEnumerable<(string FormKey, string? EditorId, string? Name, ProvenanceDto Prov, List<string>? Changes)> ConflictRows();
}

public static class DatasetConflictExtensions
{
    private sealed class Source<TDto> : IConflictSource where TDto : class, IRecordDto
    {
        public required Dataset<TDto> Ds { get; init; }
        public string Name => Ds.Name;
        public IEnumerable<(string, string?, string?, ProvenanceDto, List<string>?)> ConflictRows()
        {
            foreach (var w in Ds.Winners)
            {
                var p = w.Provenance!;
                if (p.Chain.Count < 2) continue;
                var node = Json.ToNode(w);
                Ds.ChangeDisplays.TryGetValue(w.FormKey, out var changes);
                yield return (w.FormKey,
                    node.TryGetPropertyValue("editorId", out var e) ? e?.GetValue<string>() : null,
                    node.TryGetPropertyValue("name", out var n) ? n?.GetValue<string>() : null,
                    p, changes);
            }
        }
    }

    public static IConflictSource AsConflicts<TDto>(this Dataset<TDto> ds) where TDto : class, IRecordDto
        => new Source<TDto> { Ds = ds };
}
